require('dotenv').config();
const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const logger = require('./logger');

const app = express();
const port = 3000;

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(express.static('public'));
app.set('view engine', 'ejs');

// Security Level Middleware (Env based)
app.use((req, res, next) => {
    // Read from Environment Variable. Default to 'v1' if not set.
    const envLevel = process.env.SECURITY_LEVEL || 'v1';
    req.securityLevel = envLevel;
    res.locals.securityLevel = envLevel;
    res.locals.securityLevel = envLevel;
    res.locals.user = req.cookies.user;
    res.locals.isAdmin = req.cookies.isAdmin === 'true';
    res.locals.baseUrl = `${req.protocol}://${req.get('host')}`;
    next();
});

// Logging Middleware
app.use((req, res, next) => {
    const start = Date.now();

    // Capture response status on finish
    res.on('finish', () => {
        const duration = Date.now() - start;

        // Calculate statistical features
        const numHeaders = Object.keys(req.headers).length;
        const numQueryParams = Object.keys(req.query).length;
        const numBodyKeys = req.body ? Object.keys(req.body).length : 0;
        const contentLen = req.get('content-length') ? parseInt(req.get('content-length')) : 0;
        const responseSize = res.get('content-length') ? parseInt(res.get('content-length')) : 0;

        const logData = {
            timestamp: new Date().toISOString(),
            ip: req.ip,
            method: req.method,
            url: req.originalUrl,
            headers: req.headers,
            query: req.query,
            body: req.body, // Important for capturing attack payloads
            response_status: res.statusCode,
            duration_ms: duration,
            user: req.cookies.user || 'anonymous',
            security_level: req.securityLevel,

            // Enhanced Features for NIDS/AI
            response_size: responseSize,
            referrer: req.get('referer') || '',
            user_agent: req.get('user-agent') || '',
            num_headers: numHeaders,
            num_query_params: numQueryParams,
            num_body_keys: numBodyKeys,
            request_content_length: contentLen
        };

        logger.info('Traffic Log', logData);
    });

    next();
});



// Database Setup
const db = new sqlite3.Database('vuln_shop.db');

db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        profile_image TEXT
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_name TEXT,
        price INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        image TEXT,
        description TEXT
    )`);

    // Seed Data
    db.run(`INSERT OR IGNORE INTO users (username, password) VALUES ('admin', 'admin123')`);
    db.run(`INSERT OR IGNORE INTO users (username, password) VALUES ('guest', 'guest123')`);

    // Seed Products
    db.get("SELECT count(*) as count FROM products", (err, row) => {
        if (row.count === 0) {
            const products = [
                { name: 'OVERSIZED HOODIE', price: 120.00, image: '/images/oversized-hoodie.jpg', description: 'Heavyweight cotton fleece.' },
                { name: 'VINTAGE TEE', price: 45.00, image: '/images/vintage-tee.jpg', description: 'Washed black with distressed details.' },
                { name: 'CARGO PANTS', price: 95.00, image: '/images/cargo-pants.jpg', description: 'Multi-pocket functionality.' },
                { name: 'TACTICAL VEST', price: 150.00, image: '/images/tactical-vest.jpg', description: 'Utility focused design.' },
                { name: 'DENIM JACKET', price: 180.00, image: '/images/denim-jacket.jpg', description: 'Classic cut with modern wash.' },
                { name: 'BEANIE', price: 35.00, image: '/images/beanie.jpg', description: 'Ribbed knit essential.' }
            ];
            const stmt = db.prepare("INSERT INTO products (name, price, image, description) VALUES (?, ?, ?, ?)");
            products.forEach(p => {
                stmt.run(p.name, p.price, p.image, p.description);
            });
            stmt.finalize();
        }
    });

    // Seed Orders
    db.get("SELECT count(*) as count FROM orders", (err, row) => {
        if (row.count === 0) {
            db.run(`INSERT INTO orders (user_id, product_name, price) VALUES (1, 'Cyber Hoodie', 120)`); // Admin's order
            db.run(`INSERT INTO orders (user_id, product_name, price) VALUES (2, 'Acid Wash Tee', 45)`); // Guest's order
        }
    });
});

// File Upload Config
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, 'public/uploads/')
    },
    filename: function (req, file, cb) {
        // v3: Randomize filename
        if (req.securityLevel === 'v3') {
            const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
            cb(null, uniqueSuffix + path.extname(file.originalname));
        } else {
            // v1, v2: Keep original filename (vulnerable to overwriting or predictable paths)
            cb(null, file.originalname);
        }
    }
});

const upload = multer({
    storage: storage,
    fileFilter: (req, file, cb) => {
        if (req.securityLevel === 'v3') {
            // v3: Strict Allowlist
            const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
            if (!allowedTypes.includes(file.mimetype)) {
                return cb(new Error('Only images are allowed'));
            }
        } else if (req.securityLevel === 'v2') {
            // v2: Weak check (e.g., just check extension or allow more types)
            if (file.mimetype === 'application/x-php') { // Example of weak blacklist
                return cb(new Error('PHP files not allowed'));
            }
        }
        // v1: No validation
        cb(null, true);
    }
});

// Routes

// Home
// Home
app.get('/', (req, res) => {
    db.all("SELECT * FROM products", (err, rows) => {
        res.render('index', { products: rows });
    });
});

// Login Page
app.get('/login', (req, res) => {
    res.render('login', { error: null });
});

// Login Action (SQL Injection)
app.post('/login', (req, res) => {
    const { username, password } = req.body;
    const level = req.securityLevel;

    // Check for Admin from .env
    if (username === process.env.ADMIN_USERNAME && password === process.env.ADMIN_PASSWORD) {
        res.cookie('user', username);
        res.cookie('isAdmin', 'true');
        res.cookie('user_id', 0); // Admin ID
        return res.redirect('/');
    }

    console.log(`[${level}] Login Attempt: ${username}`);

    if (level === 'v3') {
        // v3: Secure (Parameterized Query)
        db.get("SELECT * FROM users WHERE username = ? AND password = ?", [username, password], (err, row) => {
            handleLogin(err, row, res);
        });
    } else if (level === 'v2') {
        // v2: Weak Mitigation (Blacklist)
        const safeUser = username.replace(/'/g, '').replace(/--/g, '');
        const safePass = password.replace(/'/g, '').replace(/--/g, '');
        const query = `SELECT * FROM users WHERE username = '${safeUser}' AND password = '${safePass}'`;
        console.log(`[${level}] Query: ${query}`);
        db.get(query, (err, row) => {
            handleLogin(err, row, res);
        });
    } else {
        // v1: Vulnerable (String Concatenation)
        const query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'";
        console.log(`[${level}] Query: ${query}`);
        db.get(query, (err, row) => {
            handleLogin(err, row, res);
        });
    }
});

function handleLogin(err, row, res) {
    if (err) {
        console.error(err);
        return res.status(500).send("Internal Server Error");
    }
    if (row) {
        res.cookie('user', row.username);
        res.cookie('isAdmin', 'false');
        res.cookie('user_id', row.id); // Needed for IDOR check
        return res.redirect('/');
    } else {
        return res.render('login', { error: "Invalid username or password" });
    }
}

// Signup
app.get('/signup', (req, res) => {
    res.render('signup', { error: null });
});

app.post('/signup', (req, res) => {
    const { username, password } = req.body;
    db.run("INSERT INTO users (username, password) VALUES (?, ?)", [username, password], function (err) {
        if (err) {
            return res.render('signup', { error: "Username already exists" });
        }
        res.redirect('/login');
    });
});

// Logout
app.get('/logout', (req, res) => {
    res.clearCookie('user');
    res.clearCookie('isAdmin');
    res.clearCookie('user_id');
    res.redirect('/');
});

// Board (XSS)
app.get('/board', (req, res) => {
    db.all("SELECT * FROM posts ORDER BY created_at DESC", (err, rows) => {
        res.render('board', { posts: rows });
    });
});

app.post('/board', (req, res) => {
    let { content } = req.body;
    const level = req.securityLevel;

    // Input Sanitization based on level
    if (level === 'v2') {
        // v2: Weak Sanitization (Remove <script> tags only)
        content = content.replace(/<script>/gi, '');
    }

    const stmt = db.prepare("INSERT INTO posts (content) VALUES (?)");
    stmt.run(content, (err) => {
        res.redirect('/board');
    });
    stmt.finalize();
});

// Profile (File Upload)
app.get('/profile', (req, res) => {
    if (!req.cookies.user) return res.redirect('/login');
    console.log("Profile request for user:", req.cookies.user);

    db.get("SELECT * FROM users WHERE username = ?", [req.cookies.user], (err, row) => {
        if (err) {
            console.error("DB Error in profile:", err);
            return res.status(500).send("DB Error");
        }
        if (!row) {
            console.error("User not found in DB:", req.cookies.user);
            // If admin is not in DB, we might want to handle it gracefully or just error
            return res.status(500).send("User not found in DB");
        }
        res.render('profile', { user: row, msg: null });
    });
});

app.post('/profile/upload', upload.single('profile_image'), (req, res) => {
    if (!req.cookies.user) return res.redirect('/login');

    if (!req.file) {
        return res.render('profile', { user: { username: req.cookies.user }, msg: "Upload failed or invalid file." });
    }

    const filePath = '/uploads/' + req.file.filename;

    db.run("UPDATE users SET profile_image = ? WHERE username = ?", [filePath, req.cookies.user], (err) => {
        res.render('profile', { user: { username: req.cookies.user, profile_image: filePath }, msg: "Profile updated!" });
    });
});

// Order History (IDOR)
app.get('/order', (req, res) => {
    if (!req.cookies.user) return res.redirect('/login');

    const level = req.securityLevel;
    let queryId = req.query.id;

    if (!queryId) {
        db.all("SELECT * FROM orders WHERE user_id = ?", [req.cookies.user_id], (err, rows) => {
            res.render('order_list', { orders: rows });
        });
        return;
    }

    // Detail View Vulnerability Logic
    let targetId = queryId;

    if (level === 'v2') {
        // v2: Obfuscation (Base64)
        try {
            targetId = Buffer.from(queryId, 'base64').toString('ascii');
        } catch (e) {
            return res.send("Invalid ID format");
        }
    }

    let sql = "SELECT * FROM orders WHERE id = ?";
    let params = [targetId];

    if (level === 'v3') {
        sql += " AND user_id = ?";
        params.push(req.cookies.user_id);
    }

    db.get(sql, params, (err, row) => {
        if (err) return res.status(500).send("DB Error");
        if (!row) return res.status(404).send("Order not found or access denied");
        res.render('order_detail', { order: row });
    });
});

// Admin Routes
function isAdmin(req, res, next) {
    if (req.cookies.isAdmin === 'true') {
        next();
    } else {
        res.status(403).send("Access Denied");
    }
}

app.get('/admin/products', isAdmin, (req, res) => {
    db.all("SELECT * FROM products", (err, rows) => {
        res.render('admin_products', { products: rows });
    });
});

app.post('/admin/products/:id', isAdmin, (req, res) => {
    const { name, price, description } = req.body;
    db.run("UPDATE products SET name = ?, price = ?, description = ? WHERE id = ?", [name, price, description, req.params.id], (err) => {
        res.redirect('/admin/products');
    });
});

app.post('/admin/posts/:id/delete', isAdmin, (req, res) => {
    db.run("DELETE FROM posts WHERE id = ?", [req.params.id], (err) => {
        res.redirect('/board');
    });
});

app.get('/admin/users', isAdmin, (req, res) => {
    db.all("SELECT * FROM users", (err, rows) => {
        res.render('admin_users', { users: rows });
    });
});

app.post('/admin/users/:id/delete', isAdmin, (req, res) => {
    db.run("DELETE FROM users WHERE id = ?", [req.params.id], (err) => {
        res.redirect('/admin/users');
    });
});

app.listen(port, () => {
    console.log(`Vulnerable Shop (High Street Edition) listening at http://localhost:${port}`);
    console.log(`Security Level: ${process.env.SECURITY_LEVEL || 'v1 (Default)'}`);
});
