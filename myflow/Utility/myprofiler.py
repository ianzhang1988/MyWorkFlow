# -*- coding: utf-8 -*-
# @Time    : 2020/12/7 16:20
# @Author  : ZhangYang
# @Email   : ian.zhang.88@outlook.com
import cProfile
import pstats
import os
from functools import wraps


def profile(output_file=None, sort_by='cumulative', lines_to_print=None, strip_dirs=False):
    """A time profiler decorator.
    Inspired by and modified the profile decorator of Giampaolo Rodola:
    http://code.activestate.com/recipes/577817-profile-decorator/
    Args:
        output_file: str or None. Default is None
            Path of the output file. If only name of the file is given, it's
            saved in the current directory.
            If it's None, the name of the decorated function is used.
        sort_by: str or SortKey enum or tuple/list of str/SortKey enum
            Sorting criteria for the Stats object.
            For a list of valid string and SortKey refer to:
            https://docs.python.org/3/library/profile.html#pstats.Stats.sort_stats
        lines_to_print: int or None
            Number of lines to print. Default (None) is for all the lines.
            This is useful in reducing the size of the printout, especially
            that sorting by 'cumulative', the time consuming operations
            are printed toward the top of the file.
        strip_dirs: bool
            Whether to remove the leading path info from file names.
            This is also useful in reducing the size of the printout
    Returns:
        Profile of the decorated function
    """

    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _output_file = output_file or func.__name__ + '.prof'
            pr = cProfile.Profile()
            pr.enable()
            retval = func(*args, **kwargs)
            pr.disable()
            pr.dump_stats(_output_file)

            with open(_output_file, 'w') as f:
                ps = pstats.Stats(pr, stream=f)
                if strip_dirs:
                    ps.strip_dirs()
                if isinstance(sort_by, (tuple, list)):
                    ps.sort_stats(*sort_by)
                else:
                    ps.sort_stats(sort_by)
                ps.print_stats(lines_to_print)
            return retval

        return wrapper

    return inner

my_profilers = {}

def profile2(name):
    """A time profiler decorator.
    Inspired by and modified the profile decorator of Giampaolo Rodola:
    http://code.activestate.com/recipes/577817-profile-decorator/
    Args:
        output_file: str or None. Default is None
            Path of the output file. If only name of the file is given, it's
            saved in the current directory.
            If it's None, the name of the decorated function is used.
        sort_by: str or SortKey enum or tuple/list of str/SortKey enum
            Sorting criteria for the Stats object.
            For a list of valid string and SortKey refer to:
            https://docs.python.org/3/library/profile.html#pstats.Stats.sort_stats
        lines_to_print: int or None
            Number of lines to print. Default (None) is for all the lines.
            This is useful in reducing the size of the printout, especially
            that sorting by 'cumulative', the time consuming operations
            are printed toward the top of the file.
        strip_dirs: bool
            Whether to remove the leading path info from file names.
            This is also useful in reducing the size of the printout
    Returns:
        Profile of the decorated function
    """

    my_pr = cProfile.Profile()
    my_profilers[name]=my_pr

    def inner(func):
        @wraps(func)

        def wrapper(*args, **kwargs):

            my_pr.enable()
            retval = func(*args, **kwargs)
            my_pr.disable()

            return retval

        return wrapper
    return inner

def output_profile(output_path=None, sort_by='cumulative', lines_to_print=None, strip_dirs=False):

    for my_pr_name in my_profilers:
        my_pr = my_profilers[my_pr_name]
        out_file = os.path.join(output_path,"%s.prof"%my_pr_name)
        my_pr.dump_stats(out_file)
        with open(out_file, 'w') as f:
            ps = pstats.Stats(my_pr, stream=f)
            if strip_dirs:
                ps.strip_dirs()
            if isinstance(sort_by, (tuple, list)):
                ps.sort_stats(*sort_by)
            else:
                ps.sort_stats(sort_by)
            ps.print_stats(lines_to_print)