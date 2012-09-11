import time

import py


class TestTimeObject(object):
    def test_now(self, space, monkeypatch):
        monkeypatch.setattr(time, "time", lambda: 342.1)
        w_secs = space.execute("return Time.now.to_f")
        assert space.float_w(w_secs) == 342.1

    # pytest currently explodes with monkeypatching time.time
    @py.test.mark.xfail(run=False)
    def test_subtraction(self, space, monkeypatch):
        monkeypatch.setattr(time, "time", iter([18, 12]).next)
        w_secs = space.execute("return Time.now - Time.now")
        assert space.float_w(w_secs) == 6

    def test_new(self, space, monkeypatch):
        monkeypatch.setattr(time, "time", lambda: 342.1)
        w_secs = space.execute("return Time.new.to_f")
        assert space.float_w(w_secs) == 342.1
        w_secs = space.execute("return Time.new(2012).to_f")
        assert space.float_w(w_secs) == time.mktime((2012, 0, 0, 0, 0, 0, 0, 0, -1))
        w_secs = space.execute("return Time.new(2012, 11).to_f")
        assert space.float_w(w_secs) == time.mktime((2012, 11, 0, 0, 0, 0, 0, 0, -1))
        w_secs = space.execute("return Time.new(2012, 11, 3).to_f")
        assert space.float_w(w_secs) == time.mktime((2012, 11, 3, 0, 0, 0, 0, 0, -1))
        w_secs = space.execute("return Time.new(2012, 11, 3, 5).to_f")
        assert space.float_w(w_secs) == time.mktime((2012, 11, 3, 5, 0, 0, 0, 0, -1))
        w_secs = space.execute("return Time.new(2012, 11, 3, 5, 12).to_f")
        assert space.float_w(w_secs) == time.mktime((2012, 11, 3, 5, 12, 0, 0, 0, -1))
        w_secs = space.execute("return Time.new(2012, 11, 3, 5, 12, 35).to_f")
        assert space.float_w(w_secs) == time.mktime((2012, 11, 3, 5, 12, 35, 0, 0, -1))
