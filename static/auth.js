$(function(){
	$('#submite').click(function(){
		var login = $("#login").val();
		var passwd = $("#passwd").val();
		$.post("/login", {username:login,passwd:passwd})
		.done(function(response){
			location.reload();
		})
		.fail(function(){
			alert('YOU SHALL NOT PASS');
		});
	});
});
