import { action, autorun, observable } from "mobx";
import { observer } from "mobx-react";
import * as React from "react";
import * as ReactDOM from "react-dom";

interface PossibleLap {
  time: number;
  lap: boolean;
  comment: string;
}

interface TimeAttack {
  person: string;
  durations: number[];
}

declare var is_kasse_i_kass: boolean;

declare var time_attack: TimeAttack | null;

declare var initial_state: {
  elapsed_time: number;
  durations: number[];
  state: number;
  result: number;
  result_display: string;
  time_attack: TimeAttack | null;
} | null;

const possible_laps: PossibleLap[] = [];
let form: HTMLFormElement | null = null;
let roundtrip_estimate = 0;
let fetch_interval: NodeJS.Timeout | null = null;

function format_difference(total_milliseconds: number, n: number) {
  // U+2212 = Minus Sign
  const s = total_milliseconds > 0 ? "+" : "\u2212";
  if (total_milliseconds < 0) total_milliseconds = -total_milliseconds;
  const seconds = (total_milliseconds / 1000) | 0;
  const milliseconds = (total_milliseconds - 1000 * seconds) | 0;
  return s + seconds + "." + ("000" + milliseconds).slice(-3, -3 + n);
}

function format_timestamp(total_milliseconds: number, n: number) {
  const total_seconds = (total_milliseconds / 1000) | 0;
  const milliseconds = (total_milliseconds - 1000 * total_seconds) | 0;
  const total_minutes = (total_seconds / 60) | 0;
  const seconds = (total_seconds - 60 * total_minutes) | 0;
  const total_hours = (total_minutes / 60) | 0;
  const minutes = total_minutes - 60 * total_hours;
  return (
    total_hours +
    ":" +
    ("00" + minutes).slice(-2) +
    ":" +
    ("00" + seconds).slice(-2) +
    "." +
    ("000" + milliseconds).slice(-3, -3 + n)
  );
}

class State {
  @observable
  headerString = "Stopur";
  @observable
  start_time: number | null = null;
  @observable
  total_milliseconds: number | null = null;
  @observable
  stopped = true;
  @observable
  laps: number[] = [];

  get durations() {
    let prev = 0;
    const v: number[] = [];
    for (let i = 0; i < state.laps.length; ++i) {
      const duration = (state.laps[i] - prev) | 0;
      prev = state.laps[i];
      v.push(duration / 1000);
    }
    return v;
  }
}

const state = new State();

function update_time() {
  if (state.stopped) {
    state.total_milliseconds =
      state.laps.length > 0 ? state.laps[state.laps.length - 1] : 0;
  } else {
    const now = new Date().getTime();
    state.total_milliseconds = (now - (state.start_time as number)) | 0;
    window.requestAnimationFrame(update_time);
  }
}

@observer
class Stopwatch extends React.Component<{header: string}, {}> {
  render() {
    const button = state.stopped ? (
      <button onClick={() => this.onStart()}>
        {state.laps.length ? `Fortsæt med øl ${state.laps.length}` : "Start"}
      </button>
    ) : (
      <button onClick={e => this.onLap(e)} onTouchStart={e => this.onLap(e)}>
        Færdig med øl {state.laps.length + 1}
      </button>
    );
    return (
      <>
        <h1>{this.props.header}</h1>
        <div id="time">
          {format_timestamp(
            state.total_milliseconds || 0,
            state.stopped ? 2 : 1
          )}
        </div>
        <div id="buttons">{button}</div>
        {<Laps />}
      </>
    );
  }

  @action
  onStart() {
    if (state.laps.length == 0) {
      // note, too large for signed 32-bit int
      state.start_time = new Date().getTime() - (state.total_milliseconds || 0);
    }
    add_possible_lap(state.laps.length > 0 ? "Fortsæt" : "Start");
    state.stopped = false;
    post_live_update();
  }

  @action
  onLap(e: React.MouseEvent | React.TouchEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (state.start_time == null) return;
    const n = new Date().getTime();
    try_add_lap((n - state.start_time) | 0);
  }
}

function Lap({
  index,
  duration,
  total,
  difference
}: {
  index: number;
  duration: number;
  total: number;
  difference: number | null;
}) {
  let lapTotal = format_timestamp(total, 2);
  if (is_kasse_i_kass) {
    const time = new Date();
    time.setTime(total + (state.start_time as number));
    const timeStr = time + "";
    const match = /(\d+:\d+:\d+)/.exec(timeStr);
    lapTotal = match ? (match[1] as string) : "";
  }
  let lapDiff: JSX.Element;
  if (difference !== null) {
    const c = difference <= 0 ? "negdiff" : "posdiff";
    lapDiff = (
      <div className={"lapDiff " + c}>{format_difference(difference, 2)}</div>
    );
  } else {
    lapDiff = <div className="lapDiff" />;
  }
  return (
    <div className="lap">
      <div className="lapIndex">Øl {index}</div>
      <div className="lapDuration">{format_timestamp(duration, 2)}</div>
      <div className="lapTotal">{lapTotal}</div>
      {lapDiff}
    </div>
  );
}

@observer
class Laps extends React.Component<{}, {}> {
  render() {
    const laps: JSX.Element[] = [];

    let prev = 0;
    let ta_cumsum = 0;
    const v = [];
    for (let i = 0; i < state.laps.length; ++i) {
      const duration = (state.laps[i] - prev) | 0;
      prev = state.laps[i];
      v.push(duration / 1000);
      if (time_attack) {
        ta_cumsum += time_attack.durations[i] | 0;
      }
      let difference = null;
      if (time_attack) {
        if (time_attack.durations.length > i) {
          difference = (state.laps[i] - ta_cumsum) | 0;
        } else {
          difference = null;
        }
      }
      laps.push(
        <Lap
          index={i + 1}
          duration={duration}
          total={state.laps[i]}
          difference={difference}
        />
      );
    }

    const ta_len = time_attack ? time_attack.durations.length : 0;
    if (time_attack && ta_len > state.laps.length) {
      ta_cumsum += time_attack.durations[state.laps.length];
      laps.push(
        <div className="lap">
          <div className="lapIndex" />
          <div className="lapDuration" />
          <div className="lapTotal" />
          <TimeAttackCurrentDifference />
        </div>
      );
    }
    // TODO(rav): Scroll laps if applicable
    return (
      <div id="laps" className={laps.length > 8 ? "many" : ""}>
        {laps}
      </div>
    );
  }
}

@observer
class TimeAttackCurrentDifference extends React.Component<{}, {}> {
  render() {
    if (state.stopped || !time_attack) return <></>;
    let ta_cumsum = 0;
    const l = state.laps.length + 1;
    for (let i = 0; i < l; ++i) ta_cumsum += time_attack.durations[i] | 0;
    const d = (state.total_milliseconds || 0) - ta_cumsum;
    const c = d <= 0 ? "negdiff" : "posdiff";
    return (
      <div className={"lapDiff " + c}>
        {format_difference(d, state.stopped ? 2 : 1)}
      </div>
    );
  }
}

function add_possible_lap(comment: string) {
  if (state.start_time === null) return;
  const n = new Date().getTime();
  const d = (n - state.start_time) | 0;
  possible_laps.push({
    time: d,
    lap: false,
    comment: comment
  });
}

function try_add_lap(d: number) {
  let min_length = 1000;
  if (state.laps.length === 0) min_length = 3000;
  const prev_lap =
    state.laps.length === 0 ? 0 : state.laps[state.laps.length - 1];
  if (d - prev_lap < min_length) {
    possible_laps.push({
      time: d,
      lap: false,
      comment: "For kort (" + (d - prev_lap) + " < " + min_length + ")"
    });
  } else {
    possible_laps.push({
      time: d,
      lap: true,
      comment: "Tilføjet som Øl " + (1 + state.laps.length)
    });
    state.laps.push(d);
    post_live_update();
  }
}

const stop = action((ev: Event) => {
  if (state.laps.length === 0) return reset(ev);
  add_possible_lap("Stop");
  ev.preventDefault();
  ev.stopPropagation();
  state.stopped = true;
  post_live_update();
});

const reset = action((ev: Event) => {
  ev.preventDefault();
  ev.stopPropagation();
  state.stopped = true;
  add_possible_lap("Reset");
  state.start_time = null;
  state.laps = [];
  for (const l of possible_laps) l.lap = false;
  post_live_update();
});

function window_click(_ev: Event) {
  add_possible_lap("Tryk");
}

// getCookie from https://docs.djangoproject.com/en/1.4/ref/contrib/csrf/
function getCookie(name: string) {
  const cookies = (document.cookie || "").split(";").map(s => s.trim());
  for (const cookie of cookies) {
    // Does this cookie string begin with the name we want?
    if (cookie.substring(0, name.length + 1) === name + "=")
      return decodeURIComponent(cookie.substring(name.length + 1));
  }
  return null;
}
const csrftoken = getCookie("csrftoken");

declare var post_pk: number | null;
declare var fetch_pk: number | null;
declare function reverse(name: string, pk: number): string | null;
declare var $: any;

function post_live_update() {
  if (post_pk === null) return;
  const url = reverse("timetrial_liveupdate", post_pk);
  const now = new Date().getTime();
  let n;
  if (state.start_time === null) {
    n = 0;
  } else {
    n = (now - state.start_time) | 0;
  }
  const data = {
    csrfmiddlewaretoken: csrftoken,
    timetrial: post_pk,
    durations: state.durations.join(" "),
    elapsed_time: n / 1000,
    roundtrip_estimate: roundtrip_estimate / 1000,
    possible_laps: JSON.stringify(possible_laps),
    state: state.stopped
      ? state.laps.length > 0
        ? "stopped"
        : "initial"
      : "running"
  };
  function measure_roundtrip() {
    roundtrip_estimate = (new Date().getTime() - now) | 0;
    console.log("roundtrip_estimate: " + roundtrip_estimate + " ms");
  }
  $.post(url, data).always(measure_roundtrip);
}

function fetch_state() {
  const now = new Date().getTime();
  function success(data: any) {
    roundtrip_estimate = (new Date().getTime() - now) | 0;
    console.log("roundtrip_estimate: " + roundtrip_estimate + " ms");
    data["elapsed_time"] = data["elapsed_time"] + roundtrip_estimate / 2000;
    console.log(data);
    update_state(data);
  }
  function fail(_jqxhr: unknown, textStatus: string, error: any) {
    const btn = document.getElementById("live");
    if (btn) btn.textContent = "Fejl";
    (document.getElementById("stopwatchlog") as Element).appendChild(
      document.createTextNode(textStatus + ", " + error + "\n")
    );
  }
  $.getJSON(".", success).fail(fail);
}

const update_state = action((remoteState: any) => {
  const elapsed = (remoteState["elapsed_time"] * 1000) | 0;
  state.start_time = new Date().getTime() - elapsed;

  state.laps = [];
  let p = 0;
  for (const duration of remoteState["durations"]) {
    p += (1000 * duration) | 0;
    state.laps.push(p);
  }

  let button_label = "Live";
  if (remoteState["result"] === "") {
    if (remoteState["state"] === "initial") {
      state.stopped = true;
    } else if (remoteState["state"] === "running") {
      state.stopped = false;
      update_time();
    } else if (remoteState["state"] === "stopped") {
      state.stopped = true;
    }
  } else {
    state.stopped = true;
    if (fetch_interval !== null) {
      clearInterval(fetch_interval);
      fetch_interval = null;
    }
    button_label = remoteState["result_display"];
  }

  const btn = document.getElementById("live");
  if (btn) btn.textContent = button_label;
});

function takePictureChange(ev: { target: EventTarget | null }) {
  const div_pictures = document.getElementById("pictures");
  if (!div_pictures) return console.log("No #pictures");

  const showError = (s: string) => {
    div_pictures.textContent = s;
  };

  if (typeof URL === "undefined") return showError("No File API support");
  const target = ev.target as HTMLFormElement;
  if (!target.files) console.log("No target.files");
  const files = target.files || [];
  if (files.length === 0) console.log("files is empty");
  div_pictures.innerHTML = "";
  for (const file of files) {
    const imgURL = URL.createObjectURL(file);
    const img = document.createElement("img");
    img.src = imgURL;
    URL.revokeObjectURL(imgURL);
    div_pictures.appendChild(img);
  }
}

function init() {
  form = document.getElementById("stopwatch_form") as HTMLFormElement;
  const btn_stop = document.getElementById("stop");
  if (btn_stop) {
    btn_stop.addEventListener("click", stop, false);
  }
  const btn_reset = document.getElementById("reset");
  if (btn_reset) {
    btn_reset.addEventListener("click", reset, false);
  }
  if (initial_state !== null) update_state(initial_state);

  if (fetch_pk !== null) {
    fetch_interval = setInterval(fetch_state, 2000);
  }
  window.addEventListener("touchstart", window_click, false);

  const takePicture = document.getElementById("take-picture");
  if (takePicture !== null) {
    takePicture.addEventListener("change", takePictureChange, false);
    takePictureChange({ target: takePicture });
  }

  let headerString = "Stopur";
  const existingHeader = document.querySelector("#stopwatch h1");
  if (existingHeader) {
    headerString = existingHeader.textContent || headerString;
  }
  ReactDOM.render(<Stopwatch header={headerString} />, document.getElementById("stopwatch"));

  autorun(() => {
    if (!state.stopped) window.requestAnimationFrame(update_time);
  });

  autorun(() => {
    const durationString = state.durations.join(" ");
    const startTime = state.start_time ? state.start_time / 1000 : undefined;
    if (form) {
      form.durations.value = durationString;
      form.start_time.value = startTime;
    }
  });
}

window.addEventListener("load", init, false);
