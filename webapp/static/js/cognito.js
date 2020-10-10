var poolData = {
	UserPoolId: 'us-east-1_fk7ZEvP01', // Your user pool id here
	ClientId: '3j163e866pobaqkqo86hvnljv7', // Your client id here
};
var userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

function signUp() {

	var elements = document.getElementById("signup").elements;
    var obj ={};
    for(var i = 0 ; i < elements.length ; i++){
        var item = elements.item(i);
        obj[item.name] = item.value;
	}
	if(obj['password'] != obj['password_confirm']) {
		document.getElementById("flashAlert").innerHTML = 'Passwords do not match. Please try again.';
		$("#flashAlert").show();
		return;
	}

	var attributeList = [];
	var dataEmail = {
		Name: 'email',
		Value: obj['email'],
	};
	var dataName = {
		Name: 'name',
		Value: obj['name'],
	};

	var attributeEmail = new AmazonCognitoIdentity.CognitoUserAttribute(dataEmail);
	attributeList.push(attributeEmail);
	var attributeName = new AmazonCognitoIdentity.CognitoUserAttribute(dataName);
	attributeList.push(attributeName);

	userPool.signUp(obj['email'], obj['password'], attributeList, null, function (
		err,
		result
	) {
		if (err) {
			document.getElementById("flashAlert").innerHTML = err.message || JSON.stringify(err);
			$("#flashAlert").show();
			return;
		}
		var cognitoUser = result.user;
		document.getElementById("flashAlert").innerHTML = 'We have sent an email to ' + cognitoUser.getUsername() + ' for verification.';
		$("#flashAlert").show();
	});

}