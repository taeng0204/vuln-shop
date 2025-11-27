const http = require('http');
const querystring = require('querystring');

function loginAsAdmin(callback) {
    console.log("Logging in as Admin...");
    const postData = querystring.stringify({
        username: 'admin',
        password: 'admin123'
    });

    const options = {
        hostname: 'localhost',
        port: process.env.PORT || 3000,
        path: '/login',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': postData.length
        }
    };

    const req = http.request(options, (res) => {
        console.log(`Login Status: ${res.statusCode}`);
        const cookies = res.headers['set-cookie'];
        if (cookies) {
            console.log("Login Successful, Cookies received.");
            callback(cookies);
        } else {
            console.log("Login Failed, no cookies.");
        }
    });

    req.write(postData);
    req.end();
}

function verifyAdminAccess(cookies) {
    console.log("\nVerifying Admin Access to /admin/products...");
    const options = {
        hostname: 'localhost',
        port: process.env.PORT || 3000,
        path: '/admin/products',
        method: 'GET',
        headers: {
            'Cookie': cookies
        }
    };

    http.get(options, (res) => {
        console.log(`Admin Page Status: ${res.statusCode}`);
        if (res.statusCode === 200) {
            console.log("SUCCESS: Admin page accessible.");
        } else {
            console.log("FAILURE: Admin page not accessible.");
        }
    });
}

// Wait for server to restart (manual restart needed usually, but we assume running)
setTimeout(() => {
    loginAsAdmin((cookies) => {
        verifyAdminAccess(cookies);
        verifyProfileAccess(cookies);
    });
}, 2000);

function verifyProfileAccess(cookies) {
    console.log("\nVerifying Admin Profile Access...");
    const options = {
        hostname: 'localhost',
        port: process.env.PORT || 3000,
        path: '/profile',
        method: 'GET',
        headers: {
            'Cookie': cookies
        }
    };

    http.get(options, (res) => {
        console.log(`Profile Page Status: ${res.statusCode}`);
        if (res.statusCode === 200) {
            console.log("SUCCESS: Profile page accessible.");
        } else {
            console.log("FAILURE: Profile page returned " + res.statusCode);
        }
    });
}
