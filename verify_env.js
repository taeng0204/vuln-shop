const { spawn } = require('child_process');
const http = require('http');
const querystring = require('querystring');

const PORT = 3000;
const BASE_URL = `http://localhost:${PORT}`;

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function request(method, path, data, cookies) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'localhost',
            port: PORT,
            path: path,
            method: method,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': cookies ? cookies.join('; ') : ''
            }
        };

        if (data) {
            options.headers['Content-Length'] = Buffer.byteLength(data);
        }

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => resolve({ statusCode: res.statusCode, headers: res.headers, body }));
        });

        req.on('error', reject);

        if (data) req.write(data);
        req.end();
    });
}

async function testLevel(level) {
    console.log(`\n=== Testing SECURITY_LEVEL=${level} ===`);

    // Start Server with Env Var
    const server = spawn('node', ['server.js'], {
        env: { ...process.env, SECURITY_LEVEL: level },
        cwd: __dirname
    });

    let serverStarted = false;
    server.stdout.on('data', (data) => {
        const msg = data.toString();
        // console.log(`[Server] ${msg.trim()}`);
        if (msg.includes(`listening at http://localhost:${PORT}`)) {
            serverStarted = true;
        }
    });

    // Wait for server to start
    console.log("Starting server...");
    for (let i = 0; i < 10; i++) {
        if (serverStarted) break;
        await sleep(500);
    }

    if (!serverStarted) {
        console.error("Server failed to start!");
        server.kill();
        return;
    }

    try {
        // 1. Test SQL Injection
        console.log("Testing SQL Injection...");
        const loginData = querystring.stringify({ username: "admin' --", password: "any" });
        const loginRes = await request('POST', '/login', loginData);

        if (loginRes.statusCode === 302 && loginRes.headers.location === '/') {
            console.log(`  -> [${level}] SQLi: SUCCESS (Vulnerable)`);
        } else {
            console.log(`  -> [${level}] SQLi: FAILED (Secure/Mitigated)`);
        }

        // 2. Test XSS
        console.log("Testing XSS...");
        const xssPayload = `<script>alert('${level}')</script>`;
        const xssData = querystring.stringify({ content: xssPayload });
        await request('POST', '/board', xssData);
        const boardRes = await request('GET', '/board');

        if (boardRes.body.includes(xssPayload)) {
            console.log(`  -> [${level}] XSS: SUCCESS (Vulnerable)`);
        } else {
            console.log(`  -> [${level}] XSS: FAILED (Secure/Mitigated)`);
        }

    } catch (e) {
        console.error("Test Error:", e);
    } finally {
        console.log("Stopping server...");
        server.kill();
        await sleep(1000); // Wait for port to clear
    }
}

async function runAllTests() {
    // Kill any running server first
    try {
        require('child_process').execSync(`pkill -f "node server.js"`);
    } catch (e) { }

    await testLevel('v1');
    await testLevel('v2');
    await testLevel('v3');
}

runAllTests();
