$(function(){
	$('button').hover(
		function(){
			$(this).animate({opacity: 0.75}, 100)
		},
		function(){
			$(this).animate({opacity: 1}, 350);
		}
	);
	$('#call').click(function(){
		var phone = $("#phone").val();
		var protocol = $("#protocol_value").val();
		var channel = protocol + '/' + getCookie('office');
		var context = $('#context').val();
		$.post("/api/call", {from:channel,to:phone,as:'api.asofts.ru',context:context,variable:''})
		.done(function(){
			$("#phone").val('');
		});
	});
	$('#whisper').click(function(){
		var protocol = $('#protocol_value').val();
		var channel = protocol + '/' + getCookie('office');
		var phone = $('#phone').val();
		var whisper_chan = $('#whisper_chan').val();
		if(phone.length > 4){
			phone = protocol + '/' + whisper_chan + '/' + phone;
		}
		else{
			phone = protocol + '/'  + phone;
		};
		$.post("/api/chanspy", {from:phone,to:channel})
		.done(function(){
			$("#phone").val('');
		});
	});
	$('#settings').click(function(){
		if($('#settings_field').is(':visible')){
			$('#settings_field').hide();
			$(this).css('color','#000');
		}
		else{
			$('#settings_field').show();
			$(this).css('color','#808080');
		};
	});
	$('#protocol_value').change(function() {
		$('#save').show();
	});
	$('#context').change(function() {
		$('#save').show();
	});
	$('#whisper_chan').change(function() {
		$('#save').show();
	});
	$('#save').click(function(){
		var protocol = $('#protocol_value').val();
		var context = $('#context').val();
		var outline = $('#whisper_chan').val();
		$.post("/change", {protocol:protocol,context:context,outline:outline})
		.done(function(){
			$('#save').hide();
		});
	});
	$('#add_user').click(function(){
		$('#modal').show();
		$('#modal_add_user').show();
	});
	$('#change_passwd').click(function(){
		$('#modal').show();
		$('#modal_change_passwd').show();
	});
	$('#exit').click(function(){
		deleteCookie('office');
		deleteCookie('token');
		location.reload();
	});
	$('#modal_exit').click(function(){
		$('#modal_add_user').hide();
		$('#modal_change_passwd').hide();
		$('#modal').hide();
	});
	$('#change_passwd_button').click(function(){
		var newpasswd = $('#new').val();
		var re_newpasswd = $('#re_new').val();
		if(newpasswd == re_newpasswd){
			$.post("/changepasswd", {passwd:newpasswd})
			.done(function(){
				$('#new').val('');
				$('#re_new').val('');
				$('#modal').hide();
			});
		};
	});
	$('#add_user_button').click(function(){
		var login = $('#add_login').val();
		var passwd = $('#add_passwd').val();
		var office = $('#add_office').val();
		$.post("/adduser", {login:login,passwd:passwd,office:office})
		.done(function(){
			$('#add_login').val('');
			$('#add_passwd').val('');
			$('#add_office').val('');
			$('#modal').hide();
		});
	});


	function getCookie(name){
		 var matches = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"));
		return matches ? decodeURIComponent(matches[1]) : undefined;
	};
	function setCookie(name, value, options) {
		options = options || {};
		var expires = options.expires;
		if (typeof expires == "number" && expires) {
			var d = new Date();
			d.setTime(d.getTime() + expires * 1000);
			expires = options.expires = d;
		}
		if (expires && expires.toUTCString) {
			options.expires = expires.toUTCString();
		}
		value = encodeURIComponent(value);
		var updatedCookie = name + "=" + value;
		for (var propName in options) {
			updatedCookie += "; " + propName;
			var propValue = options[propName];
			if (propValue !== true) {
				updatedCookie += "=" + propValue;
			}
		}
		document.cookie = updatedCookie;
	};
	function deleteCookie(name) {
		setCookie(name, "", {expires: -1})
	};
});