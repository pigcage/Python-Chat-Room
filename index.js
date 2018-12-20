//登录窗口打开与关闭
function loginWindow(){
	document.getElementById("loginWindowOuter").style.display="block";
}
function closeLoginWindow(){
	document.getElementById("loginWindowOuter").style.display="none";
	$("#errMsg").css("display","none");
}




$(document).ready(function(){
	//检查是否登录
	var chatWindow = $("#chatWindow")
	function checkLogin(){
		if (name = localStorage.getItem("name")){
			$("#errMsg").hide();
			$("#loginWindowOuter").hide();
			$("#loginLink").hide();
			$("#loginUserName").html(name);
			$("#loginUserName").show();
			$("#quitLink").show();
			$("#welcomeText").hide();
			init();
		}
		else{
			return;
		}
	}
	checkLogin();
	//建立聊天室连接
	var socket;
	function init(){
		try{
			var host ="ws://184.170.213.206:1237/";
			socket = new WebSocket(host);
			socket.onopen = function(){
				socket.send(localStorage.getItem("name"));
			};
			socket.onmessage = function(evt){
				var message = evt.data.split(",");
				//新用户加入：消息框提示，更新在线人数和列表
				if (message[0] == "LoginInfo")
				{
					chatWindow.html(chatWindow.html() + "<p style='margin:0 4%'>" + message[1] +"加入了聊天室</p>");
				}
				//收到新消息：更新聊天窗口
				else if (message[0] == "newMessage")
				{
					//数据复原
					msg = "";
					for(i=2;i<message.length;i++){
						msg = msg + message[i] + ',';
					}
					msg = msg.slice(0,-2);
					//消息时间（本地系统时间）
					var time = new Date();
					chatWindow.html(chatWindow.html() + "<div class='message'><p>" + message[1] + "</p><p>(</p><p>" + time.toLocaleString() + "</p><p>) :</p><p style='display:block;font-weight:normal;'>" + msg + "</p></div>")
				}
				//更新在线列表和人数
				else if (message[0] == "onlineList"){
					//TODO
					//alert(message);
				}
				//用户退出：消息框提示，更新在线人数和列表
				else
				{
					chatWindow.html(chatWindow.html() + "<p style='margin:2%'>" + message[1] +"退出了聊天室</p>");
				}
			}
			socket.onclose = function(){
				chatWindow.html("你已退出聊天室，请检查网络链接");
			}
		}
		catch(ex){
			alert("建立socket遇到错误："+ex+"。请尝试重新登录。");
		}
	}
	//退出，清localStorage
	$("#quitLink").click(function(){
		socket.send("**quit**," + localStorage.getItem("name"));
		localStorage.removeItem("name");
		socket.close();
		window.location.reload();
	})
	//高度自适应
	$("body").css("height",$(window).height()+"px");
	$("#text").css("width",$(window).width()*0.96-6+"px");
	$(window).resize(function(){
		$("body").css("height",document.documentElement.clientHeight +"px");
		$("#text").css("width",$(window).width()*0.96-6+"px");
	});
	//在线列表
	var ifOpenList = false;
	$("#onlineListBtn").click(function(){
		if(!ifOpenList){
			$("#onlineList p").animate({opacity:"1"},400);
			$(".chatWindow").animate({width:"74%"},500,"swing");
			$("#onlineList").animate({width:"20%"},500,"swing",function(){ifOpenList = true;});
		}
		else{
			$("#onlineList p").animate({opacity:"0"},400);
			$(".chatWindow").animate({width:"94%"},500,"swing");
			$("#onlineList").animate({width:"0%"},500,"swing",function(){ifOpenList = false;});
		}
	});
	
	var text = $("#text");//消息输入框
	var userName;//用户名
	var password;//密码
	var ifLoged = false;//登录成功标识
	
	//清除按钮
	$("#clear").click(function(){
		$("textarea[id='text']").val("");
	});
	//发送按钮
	$("#send").click(function(){
		if(!localStorage.getItem("name")){
			alert("请先登录！");
			return;
		}
		else{
			var msg = new Object();
			msg = $("textarea[id='text']").val();
			text.focus();
			if(!msg){
				alert("发送的消息不能为空"); 
				return; 
			}
			//发送消息
			try{
				socket.send("**msg**," + localStorage.getItem("name") +"," + msg);
				$("textarea[id='text']").val("");
			} 
			catch(ex){
				alert("发送失败，请重试");
				text.val = msg;
			}
		}
	});

	//发送登录信息
	$("#loginBtn").click(function(){
		$("#errMsg").html("");
		userName = $("input[id='userName']").val();
		password = $("input[id='password']").val();
		//非空验证
		if(!(userName && password))
		{
			$("#errMsg").html("用户名与密码不能为空");
			$("#errMsg").css("display","inline");
			return;
		}
		//验证用户名密码
		var loginHost = "ws://184.170.213.206:1236";
		var loginSocket = new WebSocket(loginHost);
		loginSocket.onopen = function(msg){
			loginSocket.send(userName + "," + password);
		}
		loginSocket.onmessage = function(msg){
			//success
			if(msg.data == "1"){
				//登录写缓存，此缓存退出或关闭窗口时清除
				localStorage.setItem("name",userName);
				//以下调整登录样式
				$("#errMsg").hide();
				$("#loginWindowOuter").hide();
				$("#loginLink").hide();
				$("#loginUserName").html(userName);
				$("#loginUserName").show();
				$("#quitLink").show();
				$("#welcomeText").hide();
				//链接聊天室客户端
				init();
			}
			//false
			else{
				$("#errMsg").html("用户名或密码错误");
				$("#errMsg").show();
			}	
		}
		loginSocket.onclose = function(msg){}
	})
});

window.onbeforeunload = function(){
	localStorage.removeItem("name");
	socket.close();
}