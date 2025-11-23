const http = require('http');
const querystring = require('querystring');

const BASE_URL = 'http://localhost:3000';

async function setLevel(level) {
    return new Promise((resolve) => {
        http.get(`${BASE_URL}/set-level/${level}`, (res) => {
            // Get cookie
            const rawCookies = res.headers['set-cookie'];
            console.log(`[DEBUG] setLevel(${level}) raw cookies:`, rawCookies);

            // Parse into object to handle duplicates (last wins)
            const jar = {};
            if (rawCookies) {
                rawCookies.forEach(c => {
                    const [keyVal] = c.split(';');
                    const [key, val] = keyVal.split('=');
                    jar[key.trim()] = val;
                });
            }
            // Convert back to array
            const simpleCookies = Object.entries(jar).map(([k, v]) => `${k}=${v}`);
            console.log(`[DEBUG] setLevel(${level}) simple cookies:`, simpleCookies);
            resolve(simpleCookies);
        });
    });
}

function request(method, path, data, cookies) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'localhost',
            port: 3000,
            path: path,
            method: method,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': cookies ? cookies.join('; ') : ''
            }
        };
        console.log(`[DEBUG] Request ${method} ${path} Cookie:`, options.headers.Cookie);

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

async function testSQLi(level) {
    console.log(`\n[${level}] Testing SQL Injection...`);
    const cookies = await setLevel(level);
    const postData = querystring.stringify({ username: "admin' --", password: "any" });

    const res = await request('POST', '/login', postData, cookies);

    if (res.statusCode === 302 && res.headers.location === '/') {
        console.log(`  -> SUCCESS (Vulnerable): Logged in as admin.`);
    } else {
        console.log(`  -> FAILED (Secure/Mitigated): Login failed.`);
    }
}

async function testXSS(level) {
    console.log(`\n[${level}] Testing XSS...`);
    const cookies = await setLevel(level);
    const payload = `<script>alert('${level}')</script>`;
    const postData = querystring.stringify({ content: payload });

    await request('POST', '/board', postData, cookies);

    const res = await request('GET', '/board', null, cookies);

    if (res.body.includes(payload)) {
        console.log(`  -> SUCCESS (Vulnerable): Payload found unescaped.`);
    } else {
        console.log(`  -> FAILED (Secure/Mitigated): Payload not found or escaped.`);
    }
}

async function testIDOR(level) {
    console.log(`\n[${level}] Testing IDOR...`);
    // First login as guest to get a valid session
    let cookies = await setLevel(level);
    const loginData = querystring.stringify({ username: "guest", password: "guest123" });
    const loginRes = await request('POST', '/login', loginData, cookies);

    // Update cookies with session
    const sessionCookies = loginRes.headers['set-cookie'];
    if (sessionCookies) {
        const simpleSessionCookies = sessionCookies.map(c => c.split(';')[0]);
        cookies = cookies.concat(simpleSessionCookies);
    }

    // Target Admin's Order (ID: 1)
    let targetId = '1';
    if (level === 'v2') targetId = Buffer.from('1').toString('base64'); // MQ==

    const res = await request('GET', `/order?id=${targetId}`, null, cookies);

    if (res.body.includes('Cyber Hoodie')) { // Admin's item
        console.log(`  -> SUCCESS (Vulnerable): Viewed Admin's order.`);
    } else {
        console.log(`  -> FAILED (Secure/Mitigated): Access denied or not found.`);
    }
}

async function runTests() {
    console.log("Starting Verification...");

    // v1 Tests
    await testSQLi('v1');
    await testXSS('v1');
    await testIDOR('v1');

    // v2 Tests
    await testSQLi('v2'); // Should fail (blacklist)
    await testXSS('v2'); // Should fail (script tag removed)
    await testIDOR('v2'); // Should succeed (base64)

    // v3 Tests
    await testSQLi('v3'); // Should fail
    await testXSS('v3'); // Should fail (escaped)
    await testIDOR('v3'); // Should fail (ownership check)
}

// Wait for server
setTimeout(runTests, 2000);
