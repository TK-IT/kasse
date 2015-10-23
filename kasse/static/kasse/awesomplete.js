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

	username.style.display = 'none';
	var usernameinput = document.createElement('input');
	usernameinput.placeholder = placeholder;
	username.parentNode.insertBefore(usernameinput, username);

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
		'list': names,
		'minChars': 1,
		'filter': filter
	});
	usernameinput.addEventListener('awesomplete-select', function (ev) {
		username.selectedIndex = name_to_index[ev.text];
	}, false);
}

window.addEventListener('load', home_init, false);
