import re
from io import TextIOBase
from functools import partial

from .constants import *
from unimacro import constants
 
def make_regex(tag):
    return re.compile("^\s*" + re.escape(tag))

def make_generated(codeline):
    yield DEFAULT_TAG_BEGIN + TAG_GENERATED + "\n"
    yield str(codeline) + "\n"
    yield DEFAULT_TAG_END + TAG_GENERATED + "\n"

def process_file(io_stream :TextIOBase, tag_begin=DEFAULT_TAG_BEGIN, tag_end=DEFAULT_TAG_END):
    current_tag = None
    emitted_str = None
    process_fn = None
    buffered_str = []

    def emit(s):
        nonlocal emitted_str
        emitted_str = str(s)
        
    def set_var(var_name, var_value):
        eval_scope[var_name] = var_value
        
    def set_var_proc(var_name):
        return partial(set_var, var_name)
        
    eval_scope = {
        "emit": emit,
        "set_var": set_var,
        "set_var_proc": set_var_proc,
    }

    for line in io_stream:
        if line[-1] != "\n":
            line += "\n"

        if current_tag is not None:
            # remove tag prefix from current line
            match_continue = make_regex(tag_begin + TAG_CONTINUE).match(line)
            if match_continue:
                stripped = line[match_continue.end():]
                buffered_str.append(stripped)
                yield line
            elif make_regex(tag_begin + TAG_SKIP).match(line):
                yield line
            # find end of current tag
            elif make_regex(tag_end).match(line):
                if current_tag == TAG_GENERATED:
                    buffered_str = []
                    # just ignore, dont yield
                elif current_tag == TAG_EXEC:
                    exec("\n".join(buffered_str), eval_scope)
                    yield line
                elif current_tag == TAG_PROCESS:
                    retval = process_fn("\n".join(buffered_str))
                    if retval is not None:
                        emit(retval)
                    yield line
                else:
                    # unknown tag
                    yield line
                current_tag = None
            else:
                # we are in the body of a tag
                buffered_str.append(line)
                if current_tag != TAG_GENERATED:
                    yield line
            
            if emitted_str is not None:
                yield from make_generated(emitted_str)
                emitted_str = None
                
            continue
        
        # current_tag is None
        # find begin of multiline tag
        found = None
        for tag in MULTILINE_TAGS:
            found = make_regex(tag_begin + tag).match(line)
            if found:
                if current_tag is not None:
                    raise ValueError("Tag already opened: " + current_tag)
                current_tag = tag
                buffered_str = []
                
                if tag != TAG_GENERATED:
                    yield line
                    
                if tag == TAG_PROCESS:
                    fn_str = line[found.end():].strip()
                    process_fn = eval(fn_str, eval_scope)
                    
                break
            
        if found:
            continue

        # eval tag is always single line
        match_eval = make_regex(tag_begin + TAG_EVAL).match(line)
        if match_eval:
            end_pos = match_eval.end()
            code_to_eval = line[end_pos:].strip()
            result = str(eval(code_to_eval, eval_scope))
            yield line
            yield from make_generated(result)
            continue
        
        match_exec = make_regex(tag_begin + TAG_EXEC_INLINE).match(line)
        if match_exec:
            yield line
            end_pos = match_exec.end()
            code_to_exec = line[end_pos:].strip()
            exec(code_to_exec, eval_scope)
            if emitted_str is not None:
                yield from make_generated(emitted_str)
                emitted_str = None

            continue
        
        # no multiline tag found
        yield line
        
    if current_tag is not None:
        raise ValueError("Tag not closed: " + current_tag)

    if emitted_str is not None:
        yield from make_generated(emitted_str)
        
 