import re
from io import TextIOBase
from functools import partial

from .constants import *

 
def make_regex(tag):
    return re.compile("^\s*" + re.escape(tag))

def process_file(io_stream :TextIOBase, tag_begin=DEFAULT_TAG_BEGIN, tag_end=DEFAULT_TAG_END, strip=False, **kwargs):
    current_tag = None
    emitted_str = ""
    process_fn = None
    buffered_str = []
    
    def get_indent():
        return eval_scope["INDENT"]
    
    def set_indent(indent):
        eval_scope["INDENT"] = indent
    
    def make_generated(codelines, strip=False):
        if not strip:
            yield get_indent() + tag_begin + TAG_GENERATED + INFO_GENERATED + "\n"
        yield str(codelines)
        if not strip:
            yield get_indent() + tag_end + TAG_GENERATED + INFO_GENERATED + "\n"

    def emit(s):
        nonlocal emitted_str
        emitted_str += get_indent() + str(s) + "\n"
        
    def set_var(var_name, var_value):
        eval_scope[var_name] = var_value
        
    def set_var_proc(var_name):
        return partial(set_var, var_name)
    
    def use_proc(proc):
        proc(eval_scope)
        
    eval_scope = {
        "EMIT": emit,
        "SET": set_var,
        "STORE_BLOCK": set_var_proc,
        "USE": use_proc,
        "INDENT": "",
    }
    
    eval_scope["ENV"] = eval_scope
    
    if kwargs:
        eval_scope.update(kwargs)

    for line in io_stream:
        if line[-1] != "\n":
            line += "\n"

        if current_tag is not None:
            # remove tag prefix from current line
            match_continue = make_regex(tag_begin + TAG_CONTINUE).match(line)
            if match_continue:
                stripped = line[match_continue.end():]
                buffered_str.append(stripped)
                if not strip: yield line
            elif make_regex(tag_begin + TAG_SKIP).match(line):
                if not strip: yield line

            # find end of current tag
            elif make_regex(tag_end).match(line):
                set_indent(re.match(r"^\s*", line).group())
                if current_tag == TAG_GENERATED:
                    buffered_str = []
                    # just ignore, dont yield
                elif current_tag == TAG_EXEC:
                    exec("".join(buffered_str), eval_scope)
                    if not strip: yield line
                elif current_tag == TAG_PROCESS:
                    retval = process_fn("".join(buffered_str))
                    if retval is not None:
                        emit(retval)
                    if not strip: yield line
                else:
                    # unknown tag
                    if not strip: yield line
                current_tag = None
            else:
                # we are in the body of a tag
                buffered_str.append(line)
                if current_tag != TAG_GENERATED and not strip:
                    yield line
            
            if len(emitted_str) > 0:
                yield from make_generated(emitted_str, strip)
                emitted_str = ""
                
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
                
                if tag != TAG_GENERATED and not strip:
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
            set_indent(re.match(r"^\s*", line).group())
            end_pos = match_eval.end()
            code_to_eval = line[end_pos:].strip()
            result = str(eval(code_to_eval, eval_scope))
            emit(result)
            if not strip: yield line
            yield from make_generated(emitted_str, strip)
            emitted_str = ""
            continue
        
        match_exec = make_regex(tag_begin + TAG_EXEC_INLINE).match(line)
        if match_exec:
            set_indent(re.match(r"^\s*", line).group())
            if not strip: yield line
            end_pos = match_exec.end()
            code_to_exec = line[end_pos:].strip()
            exec(code_to_exec, eval_scope)
            if len(emitted_str) > 0:
                yield from make_generated(emitted_str, strip)
                emitted_str = ""
            continue
        
        # no multiline tag found
        yield line
        
    if current_tag is not None:
        raise ValueError("Tag not closed: " + current_tag)

    if len(emitted_str) > 0:
        yield from make_generated(emitted_str, strip)
