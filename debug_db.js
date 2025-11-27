const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('vuln_shop.db');

db.serialize(() => {
    db.all("SELECT * FROM users", (err, rows) => {
        console.log("Users:", rows);
    });
    db.get("SELECT * FROM users WHERE username = ?", ['admin'], (err, row) => {
        console.log("Admin search result:", row);
    });
});
