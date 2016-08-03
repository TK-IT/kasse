// vim:set ft=javascript sw=4 sts=4 ts=4 et:
let start_time = null;
let stopped = true;
let laps = [];
const possible_laps = [];
let div_time = null;
let div_stopwatch = null;
let div_laps = null;
let btn_lap = null;
let btn_continue = null;
let form = null;
let roundtrip_estimate = 0;
let fetch_interval = null;

let ta_current = null;

function format_difference(total_milliseconds, n) {
    const s = (total_milliseconds > 0) ? '+' : '&minus;';
    if (total_milliseconds < 0) total_milliseconds = -total_milliseconds;
    const seconds = (total_milliseconds / 1000)|0;
    const milliseconds = (total_milliseconds - 1000 * seconds)|0;
    return (
        s + seconds + '.' +
        ('000' + milliseconds).slice(-3, -3 + n)
    );
}

function format_timestamp(total_milliseconds, n) {
    const total_seconds = (total_milliseconds / 1000)|0;
    const milliseconds = (total_milliseconds - 1000 * total_seconds)|0;
    const total_minutes = (total_seconds / 60)|0;
    const seconds = (total_seconds - 60 * total_minutes)|0;
    const total_hours = (total_minutes / 60)|0;
    const minutes = total_minutes - 60 * total_hours;
    return (
        total_hours + ':' +
        ('00' + minutes).slice(-2) + ':' +
        ('00' + seconds).slice(-2) + '.' +
        ('000' + milliseconds).slice(-3, -3 + n)
    );
}

function update_div_time(total_milliseconds, n) {
    const time_string = format_timestamp(total_milliseconds, n);
    div_time.textContent = time_string;
    update_ta_current(total_milliseconds, n);
}

function update_time() {
    if (!stopped) {
        const now = new Date().getTime();
        const total_milliseconds = (now - start_time)|0;
        update_div_time(total_milliseconds, 1);
        window.requestAnimationFrame(update_time);
    }
}

function lap_element(index, duration, total, difference) {
    const o = document.createElement('div');
    o.className = 'lap';
    let h = (
        '<div class="lapIndex">Øl ' + index + '</div>' +
        '<div class="lapDuration">' + format_timestamp(duration, 2) + '</div>' +
        '<div class="lapTotal">' + format_timestamp(total, 2) + '</div>'
    );
    if (difference !== null) {
        const c = (difference <= 0) ? "negdiff" : "posdiff";
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
    let prev = 0;
    let ta_cumsum = 0;
    const v = [];
    for (let i = 0; i < laps.length; ++i) {
        const duration = (laps[i] - prev)|0;
        prev = laps[i];
        v.push(duration / 1000);
        if (time_attack) {
            ta_cumsum += time_attack.durations[i] | 0;
        }
        let difference = null;
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
    const ta_len = time_attack ? time_attack.durations.length : 0;
    if (time_attack && ta_len > laps.length) {
        ta_cumsum += time_attack.durations[laps.length];
        const h = (
            '<div class="lapIndex"></div><div class="lapDuration"></div>' +
            '<div class="lapTotal"></div><div class="lapDiff" ' +
            ' id="ta_current"></div>');
        const o = document.createElement('div');
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
    let ta_cumsum = 0;
    const l = laps.length + 1;
    for (let i = 0; i < l; ++i) ta_cumsum += time_attack.durations[i]|0;
    const d = now - ta_cumsum;
    const c = (d <= 0) ? "negdiff" : "posdiff";
    ta_current.className = 'lapDiff ' + c;
    ta_current.innerHTML = format_difference(d, n);
}

function start(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    start_time = new Date().getTime(); // note, too large for signed 32-bit int
    add_possible_lap("Start");
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
    const n = new Date().getTime();
    try_add_lap((n - start_time)|0);
}

function lap_touchstart(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    const n = new Date().getTime();
    try_add_lap((n - start_time)|0);
}

function add_possible_lap(comment) {
    if (start_time === null) return;
    const n = new Date().getTime();
    const d = (n - start_time) | 0;
    possible_laps.push({
        'time': d,
        'lap': false,
        'comment': comment
    });
    console.log(possible_laps);
}

function try_add_lap(d) {
    let min_length = 1000;
    if (laps.length === 0) min_length = 3000;
    const prev_lap = (laps.length === 0) ? 0 : laps[laps.length - 1];
    if (d - prev_lap < min_length) {
        possible_laps.push({
            'time': d,
            'lap': false,
            'comment': "For kort (" + (d - prev_lap) + " < " + min_length + ")"
        });
    } else {
        possible_laps.push({
            'time': d,
            'lap': true,
            'comment': "Tilføjet som Øl " + (1 + laps.length),
        });
        laps.push(d);
        update_laps();
        post_live_update();
    }
}

function stop(ev) {
    if (laps.length === 0) return reset(ev);
    add_possible_lap("Stop");
    ev.preventDefault();
    ev.stopPropagation();
    stopped = true;
    update_div_time(laps[laps.length - 1], 2);
    div_stopwatch.className = 'stopped';
    post_live_update();
}

function reset(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    stopped = true;
    add_possible_lap("Reset");
    start_time = null;
    laps = [];
    for (let i = 0; i < possible_laps.length; i += 1) {
        possible_laps[i].lap = false;
    }
    update_laps();
    div_stopwatch.className = 'initial';
    update_div_time(0, 2);
    post_live_update();
}

function continue_(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    stopped = false;
    add_possible_lap("Fortsæt");
    window.requestAnimationFrame(update_time);
    div_stopwatch.className = 'running';
    post_live_update();
}

function window_click(ev) {
    add_possible_lap("Tryk");
}

// getCookie from https://docs.djangoproject.com/en/1.4/ref/contrib/csrf/
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie != '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

function post_live_update() {
    if (post_pk === null) return;
    const url = reverse('timetrial_liveupdate', post_pk);
    const now = new Date().getTime();
    let n;
    if (start_time === null) {
        n = 0;
    } else {
        n = (now - start_time)|0;
    }
    const data = {
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
    const now = new Date().getTime();
    function success(data) {
        roundtrip_estimate = (new Date().getTime() - now)|0;
        console.log("roundtrip_estimate: "+roundtrip_estimate+" ms");
        data['elapsed_time'] = (
            data['elapsed_time'] + roundtrip_estimate / 2000);
        console.log(data);
        update_state(data);
    }
    function fail(jqxhr, textStatus, error) {
        const btn = document.getElementById('live');
        if (btn) btn.textContent = 'Fejl';
        document.getElementById('stopwatchlog').appendChild(
            document.createTextNode(textStatus + ', ' + error + '\n'));
    }
    $.getJSON('.', success).fail(fail);
}

function update_state(state) {
    const elapsed = (state['elapsed_time'] * 1000)|0;
    start_time = new Date().getTime() - elapsed;

    laps = [];
    let p = 0;
    for (let i = 0; i < state['durations'].length; ++i) {
        const l = (1000 * state['durations'][i])|0;
        p += l;
        laps.push(p);
    }
    update_laps();

    let button_label = 'Live';
    div_stopwatch.className = state['state'];
    if (state['result'] === '') {
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
        }
    } else {
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
        button_label = state['result_display'];
    }

    const btn = document.getElementById('live');
    if (btn) btn.textContent = button_label;
}

function takePictureChange(ev) {
    function showError(s) {
        div_pictures.textContent = s;
    }

    const div_pictures = document.getElementById('pictures');
    if (!div_pictures) return console.log("No #pictures");
    if (typeof URL === 'undefined') return showError('No File API support');
    if (!ev.target.files) console.log("No ev.target.files");
    const files = ev.target.files || [];
    if (files.length === 0) console.log("files is empty");
    div_pictures.innerHTML = '';
    for (let i = 0; i < files.length; ++i) {
        const file = files[i];
        const imgURL = URL.createObjectURL(file);
        const img = document.createElement('img');
        img.src = imgURL;
        URL.revokeObjectURL(imgURL);
        div_pictures.appendChild(img);
    }
}

function init() {
    div_stopwatch = document.getElementById('stopwatch');
    div_time = document.getElementById('time');
    div_laps = document.getElementById('laps');
    form = document.getElementById('stopwatch_form');
    btn_lap = document.getElementById('lap');
    const btn_start = document.getElementById('start');
    if (btn_start) {
        btn_start.addEventListener('click', start, false);
        btn_start.addEventListener('touchstart', start, false);
    }
    if (btn_lap) {
        btn_lap.addEventListener('click', lap, false);
        btn_lap.addEventListener('touchstart', lap_touchstart, false);
    }
    const btn_stop = document.getElementById('stop');
    if (btn_stop) {
        btn_stop.addEventListener('click', stop, false);
    }
    const btn_reset = document.getElementById('reset');
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
    window.addEventListener('touchstart', window_click, false);

    const takePicture = document.getElementById('take-picture');
    if (takePicture !== null) {
        takePicture.addEventListener('change', takePictureChange, false);
        takePictureChange({target: takePicture});
    }
}

window.addEventListener('load', init, false);
