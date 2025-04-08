const jwt = require("jsonwebtoken");

const authenticateAdmin = (req, res, next) => {
  const token = req.headers.authorization;
  if (!token) return res.status(403).json({ error: "Akses ditolak" });
  jwt.verify(token, "SECRET_KEY", (err, user) => {
    if (err || !user.isAdmin) return res.status(403).json({ error: "Akses ditolak" });
    req.user = user;
    next();
  });
};