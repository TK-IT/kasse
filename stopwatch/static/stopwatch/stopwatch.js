// vim:set sw=4 sts=4 ts=4 et:
var start_time = null;
var stopped = true;
var laps = [];
var div_time = null;
var div_stopwatch = null;
var div_laps = null;
var btn_lap = null;
var btn_continue = null;
var form = null;
var roundtrip_estimate = 0;
var fetch_interval = null;

var ta_current = null;

function format_difference(total_milliseconds, n) {
    var s = (total_milliseconds > 0) ? '+' : '&minus;';
    if (total_milliseconds < 0) total_milliseconds = -total_milliseconds;
    var seconds = (total_milliseconds / 1000)|0;
    var milliseconds = (total_milliseconds - 1000 * seconds)|0;
    return (
        s + seconds + '.' +
        ('000' + milliseconds).slice(-3, -3 + n)
    );
}

function format_timestamp(total_milliseconds, n) {
    var total_seconds = (total_milliseconds / 1000)|0;
    var milliseconds = (total_milliseconds - 1000 * total_seconds)|0;
    var total_minutes = (total_seconds / 60)|0;
    var seconds = (total_seconds - 60 * total_minutes)|0;
    var total_hours = (total_minutes / 60)|0;
    var minutes = total_minutes - 60 * total_hours;
    return (
        total_hours + ':' +
        ('00' + minutes).slice(-2) + ':' +
        ('00' + seconds).slice(-2) + '.' +
        ('000' + milliseconds).slice(-3, -3 + n)
    );
}

function update_div_time(total_milliseconds, n) {
    var time_string = format_timestamp(total_milliseconds, n);
    div_time.textContent = time_string;
    update_ta_current(total_milliseconds, n);
}

function update_time() {
    if (!stopped) {
        var now = new Date().getTime();
        var total_milliseconds = (now - start_time)|0;
        update_div_time(total_milliseconds, 1);
        window.requestAnimationFrame(update_time);
    }
}

function lap_element(index, duration, total, difference) {
    var o = document.createElement('div');
    o.className = 'lap';
    var h = (
        '<div class="lapIndex">Øl ' + index + '</div>' +
        '<div class="lapDuration">' + format_timestamp(duration, 2) + '</div>' +
        '<div class="lapTotal">' + format_timestamp(total, 2) + '</div>'
    );
    if (difference !== null) {
        var c = (difference <= 0) ? "negdiff" : "posdiff";
        h += ('<div class="lapDiff ' + c + '">' +
              format_difference(difference, 2) + '</div>');
    } else {
        h += ('<div class="lapDiff"></div>');
    }
    o.innerHTML = h;
    return o;
}

function update_laps() {
    div_laps.innerHTML = '';
    var prev = 0;
    var ta_cumsum = 0;
    var v = [];
    for (var i = 0; i < laps.length; ++i) {
        var duration = (laps[i] - prev)|0;
        prev = laps[i];
        v.push(duration / 1000);
        if (time_attack) {
            ta_cumsum += time_attack.durations[i] | 0;
        }
        var difference = null;
        if (time_attack) {
            if (time_attack.durations.length > i) {
                difference = (laps[i] - ta_cumsum) | 0;
            } else {
                difference = null;
            }
        }
        div_laps.appendChild(
            lap_element(i + 1, duration, laps[i], difference));
    }
    div_laps.className = (laps.length > 8) ? 'many' : '';

    ta_current = null;
    var ta_len = time_attack ? time_attack.durations.length : 0;
    if (time_attack && ta_len > laps.length) {
        ta_cumsum += time_attack.durations[laps.length];
        var h = (
            '<div class="lapIndex"></div><div class="lapDuration"></div>' +
            '<div class="lapTotal"></div><div class="lapDiff" ' +
            ' id="ta_current"></div>');
        var o = document.createElement('div');
        o.className = 'lap';
        o.innerHTML = h;
        div_laps.appendChild(o);
        ta_current = document.getElementById('ta_current');
    }

    if (btn_lap !== null) {
        btn_lap.textContent = 'Færdig med øl '+(1 + laps.length);
    }
    if (btn_continue !== null) {
        btn_continue.textContent = 'Fortsæt med øl ' + (1 + laps.length);
    }
    if (form) {
        form.durations.value = v.join(' ');
        form.start_time.value = start_time / 1000;
    }
}

function update_ta_current(now, n) {
    if (!ta_current) return;
    ta_current.style.display = stopped ? 'none' : '';
    var ta_cumsum = 0;
    var l = laps.length + 1;
    for (var i = 0; i < l; ++i) ta_cumsum += time_attack.durations[i]|0;
    var d = now - ta_cumsum;
    var c = (d <= 0) ? "negdiff" : "posdiff";
    ta_current.className = 'lapDiff ' + c;
    ta_current.innerHTML = format_difference(d, n);
}

function start(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    start_time = new Date().getTime(); // note, too large for signed 32-bit int
    stopped = false;
    div_stopwatch.className = 'running';
    window.requestAnimationFrame(update_time);
    if (btn_lap) btn_lap.focus();
    update_laps();
    post_live_update();
}

function lap(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    var n = new Date().getTime();
    laps.push((n - start_time)|0);
    update_laps();
    post_live_update();
}

function lap_touchstart(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    var n = new Date().getTime();
    laps.push((n - start_time)|0);
    update_laps();
    post_live_update();
}

function stop(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    stopped = true;
    if (laps.length > 0) {
        update_div_time(laps[laps.length - 1], 2);
    }
    div_stopwatch.className = 'stopped';
    post_live_update();
}

function reset(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    stopped = true;
    start_time = null;
    laps = [];
    update_laps();
    div_stopwatch.className = 'initial';
    update_div_time(0, 2);
    post_live_update();
}

function continue_(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    stopped = false;
    window.requestAnimationFrame(update_time);
    div_stopwatch.className = 'running';
    post_live_update();
}

// getCookie from https://docs.djangoproject.com/en/1.4/ref/contrib/csrf/
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function post_live_update() {
    if (post_pk === null) return;
    var url = reverse('timetrial_liveupdate', post_pk);
    var now = new Date().getTime();
    var n;
    if (start_time === null) {
        n = 0;
    } else {
        n = (now - start_time)|0;
    }
    var data = {
        'csrfmiddlewaretoken': csrftoken,
        'timetrial': post_pk,
        'durations': form.durations.value,
        'elapsed_time': n / 1000,
        'roundtrip_estimate': roundtrip_estimate / 1000,
        'state': div_stopwatch.className
    };
    function measure_roundtrip() {
        roundtrip_estimate = (new Date().getTime() - now)|0;
        console.log("roundtrip_estimate: "+roundtrip_estimate+" ms");
    };
    $.post(url, data).always(measure_roundtrip);
}

function fetch_state() {
    var now = new Date().getTime();
    function success(data) {
        roundtrip_estimate = (new Date().getTime() - now)|0;
        console.log("roundtrip_estimate: "+roundtrip_estimate+" ms");
        data['elapsed_time'] = (
            data['elapsed_time'] + roundtrip_estimate / 2000);
        console.log(data);
        update_state(data);
    }
    function fail() {
        var btn = document.getElementById('live');
        if (btn) btn.textContent = 'Fejl';
    }
    $.getJSON('.', success).fail(fail);
}

function update_state(state) {
    var elapsed = (state['elapsed_time'] * 1000)|0;
    start_time = new Date().getTime() - elapsed;

    laps = [];
    var p = 0;
    for (var i = 0; i < state['durations'].length; ++i) {
        var l = (1000 * state['durations'][i])|0;
        p += l;
        laps.push(p);
    }
    update_laps();

    div_stopwatch.className = state['state'];
    if (state['state'] === 'initial') {
        stopped = true;
        update_div_time(0, 2);
    } else if (state['state'] === 'running') {
        stopped = false;
        update_time();
    } else if (state['state'] === 'stopped') {
        stopped = true;
        if (laps.length > 0) {
            update_div_time(laps[laps.length - 1], 2);
        } else {
            update_div_time(elapsed, 2);
        }
    } else if (state['state'] === 'f') {
        stopped = true;
        if (laps.length > 0) {
            update_div_time(laps[laps.length - 1], 2);
        } else {
            update_div_time(elapsed, 2);
        }
        if (fetch_interval !== null) {
            clearInterval(fetch_interval);
            fetch_interval = null;
        }
        var btn = document.getElementById('live');
        if (btn) btn.textContent = 'Færdig';
    } else if (state['state'] === 'dnf') {
        stopped = true;
        if (laps.length > 0) {
            update_div_time(laps[laps.length - 1], 2);
        } else {
            update_div_time(elapsed, 2);
        }
        if (fetch_interval !== null) {
            clearInterval(fetch_interval);
            fetch_interval = null;
        }
        var btn = document.getElementById('live');
        if (btn) btn.textContent = 'DNF';
    }
}

function init() {
    div_stopwatch = document.getElementById('stopwatch');
    div_time = document.getElementById('time');
    div_laps = document.getElementById('laps');
    form = document.getElementById('stopwatch_form');
    btn_lap = document.getElementById('lap');
    var btn_start = document.getElementById('start');
    if (btn_start) {
        btn_start.addEventListener('click', start, false);
        btn_start.addEventListener('touchstart', start, false);
    }
    if (btn_lap) {
        btn_lap.addEventListener('click', lap, false);
        btn_lap.addEventListener('touchstart', lap_touchstart, false);
    }
    var btn_stop = document.getElementById('stop');
    if (btn_stop) {
        btn_stop.addEventListener('click', stop, false);
    }
    var btn_reset = document.getElementById('reset');
    if (btn_reset) {
        btn_reset.addEventListener('click', reset, false);
    }
    btn_continue = document.getElementById('continue');
    if (btn_continue) {
        btn_continue.addEventListener('click', continue_, false);
    }
    if (initial_state !== null) update_state(initial_state);

    if (fetch_pk !== null) {
        fetch_interval = setInterval(fetch_state, 2000);
    }
}

window.addEventListener('load', init, false);
