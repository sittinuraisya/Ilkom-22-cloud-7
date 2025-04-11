const express = require('express');
const router = express.Router();
const {
  getUser,
  updateUser,
  updatePassword,
  deleteUser,
  getUsers
} = require('../controllers/userController');
const { protect, authorize } = require('../middleware/auth');

// Protected routes for all users
router.use(protect);

router.get('/me', getUser);
router.put('/update', updateUser);
router.put('/updatepassword', updatePassword);
router.delete('/delete', deleteUser);

// Admin-only routes
router.use(authorize('admin'));

router.get('/', getUsers);

module.exports = router;
