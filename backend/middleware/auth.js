const isAdmin = (req, res, next) => {
    const { email } = req.body; // Ambil dari login form
    if (email.endsWith("@kampus.com")) { // Cek email admin
      next();
    } else {
      res.status(403).json({ error: "Akses ditolak" });
    }
  };