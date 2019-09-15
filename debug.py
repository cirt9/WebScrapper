from inspect import getframeinfo, stack


def debug_info(message):
    frame_info = getframeinfo(stack()[1][0])
    return f'{frame_info.filename}:{frame_info.lineno} - {message}'
