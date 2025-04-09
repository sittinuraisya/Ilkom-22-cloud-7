const express = require('express');
const router = express.Router();
const { check } = require('express-validator');
const adminController = require('../controllers/adminController');
const auth = require('../middleware/auth');

// @route   POST api/admin/register
// @desc    Register an admin
// @access  Public
router.post(
  '/register',
  [
    check('name', 'Name is required').not().isEmpty(),
    check('email', 'Please include a valid email').isEmail(),
    check('password', 'Password must be 6 or more characters').isLength({ min: 6 }),
  ],
  adminController.registerAdmin
);

// @route   POST api/admin/login
// @desc    Login admin and get token
// @access  Public
router.post(
  '/login',
  [
    check('email', 'Please include a valid email').isEmail(),
    check('password', 'Password is required').exists(),
  ],
  adminController.loginAdmin
);

// @route   GET api/admin/me
// @desc    Get current admin
// @access  Private
router.get('/me', auth, adminController.getAdmin);

module.exports = router;