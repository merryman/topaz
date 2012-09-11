import time
import os

from pypy.rpython.tool import rffi_platform
from pypy.rpython.lltypesystem import rffi, lltype
from pypy.translator.tool.cbuild import ExternalCompilationInfo

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object
from rupypy.objects.exceptionobject import W_ArgumentError


class W_TimeObject(W_Object):
    classdef = ClassDef("Time", W_Object.classdef)

    def __init__(self, space, klass):
        W_Object.__init__(self, space, klass)
        self.epoch_seconds = 0

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_TimeObject(space, self)

    @classdef.singleton_method("now")
    def method_now(self, space):
        return space.send(self, space.newsymbol("new"))

    @classdef.method("initialize")
    def method_initialize(self, space, args_w):
        if not args_w:
            self.epoch_seconds = time.time()
        elif len(args_w) > 7:
            raise space.error(
                space.getclassfor(W_ArgumentError),
                "wrong number of arguments (%d for 1..7)" % len(args_w)
            )
        else:
            mktime_args = [space.int_w(i) for i in args_w[:6]]
            mktime_args += [0] * (6 - len(mktime_args)) # year,mon,mday,hour,min,sec
            self.epoch_seconds = _mktime(mktime_args) + mktime_args[5] % 1
            if len(args_w) == 7:
                raise NotImplementedError("UTC offset in Time.new")
        return self

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(self.epoch_seconds)

    @classdef.method("-")
    def method_sub(self, space, w_other):
        assert isinstance(w_other, W_TimeObject)
        return space.newfloat(self.epoch_seconds - w_other.epoch_seconds)


class CConfig:
    _includes = ["time.h"]
    tm_struct_fields = [("tm_sec", rffi.INT), ("tm_min", rffi.INT), ("tm_hour", rffi.INT),
                        ("tm_mday", rffi.INT), ("tm_mon", rffi.INT), ("tm_year", rffi.INT),
                        ("tm_wday", rffi.INT), ("tm_yday", rffi.INT), ("tm_isdst", rffi.INT)]
    if os.name == "nt":
        calling_conv = "win"
    else:
        calling_conv = "c"
        _includes.append('sys/time.h')
        tm_struct_fields += [("tm_gmtoff", rffi.LONG), ("tm_zone", rffi.CCHARP)]

    _compilation_info_ = ExternalCompilationInfo(includes=_includes)
    tm_struct_t = rffi_platform.Struct("struct tm", tm_struct_fields)

class cConfig:
    pass

for k, v in rffi_platform.configure(CConfig).items():
    setattr(cConfig, k, v)
cConfig.tm_struct_t.__name__ = "_tm"

c_mktime = rffi.llexternal(
    "mktime",
    [lltype.Ptr(cConfig.tm_struct_t)],
    rffi.TIME_T,
    compilation_info=CConfig._compilation_info_,
    calling_conv=CConfig.calling_conv
)

def _mktime(tup):
    assert len(tup) == 6
    buf = lltype.malloc(cConfig.tm_struct_t, flavor='raw', zero=True)
    tm_mday = tup[2]
    if tm_mday == 0:
        tm_mday = 1
    tm_month = tup[1] - 1
    if tm_month < 0:
        tm_month = 0
    rffi.setintfield(buf, 'c_tm_year', tup[0] - 1900)
    rffi.setintfield(buf, 'c_tm_mon', tm_month)
    rffi.setintfield(buf, 'c_tm_mday', tm_mday)
    rffi.setintfield(buf, 'c_tm_hour', tup[3])
    rffi.setintfield(buf, 'c_tm_min', tup[4])
    rffi.setintfield(buf, 'c_tm_sec', tup[5])
    rffi.setintfield(buf, 'c_tm_wday', -1)
    rffi.setintfield(buf, 'c_tm_yday', -1)
    rffi.setintfield(buf, 'c_tm_isdst', -1)
    tt = c_mktime(buf)
    lltype.free(buf, flavor='raw')
    return tt
