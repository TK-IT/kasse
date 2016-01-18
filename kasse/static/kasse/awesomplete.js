function home_init() {
	var username = document.querySelector('select[name=profile]');
	if (!username) return;
	var names = [];
	var name_to_index = {};
	var options = [].slice.call(username.options);
	var placeholder = '';
	for (var i = 0; i < options.length; ++i) {
		var name = options[i].textContent;
		var value = options[i].value;
		if (value === "") {
			placeholder = name;
		} else {
			names.push(name);
			name_to_index[name] = i;
		}
	}

	var usernameinput = document.getElementById('profile_text');
	username.style.display = 'none';
	usernameinput.style.display = '';
	usernameinput.placeholder = placeholder;

	var regExpEscape = Awesomplete.$.regExpEscape;

	function canonicalize(s) {
		var a = '$⁰¹²³⁴⁵⁶⁷⁸⁹';
		var b = 'S0123456789';
		var p = [].slice.call(a).map(regExpEscape).join('|');
		var re = new RegExp('(' + p + ')', 'g');
		function lookup(match) { return b.charAt(a.indexOf(match)); }
		return s.replace(re, lookup);
	}

	function filter(text, input) {
		input = canonicalize(input.trim());
		text = canonicalize(text);
		return RegExp('(^| )[KGBOT0-9]*(FU)?' + regExpEscape(input), "i").test(text);
	}

	var a = new Awesomplete(usernameinput, {
		'autoFirst': true,
		'list': names,
		'minChars': 1,
		'filter': filter
	});

	function update_select(text) {
		username.selectedIndex = name_to_index[text];
	}

	usernameinput.addEventListener('awesomplete-select', function (ev) {
		update_select(ev.text);
	}, false);

	if (usernameinput.value !== '') {
		update_select(usernameinput.value);
	}
}

window.addEventListener('load', home_init, false);
