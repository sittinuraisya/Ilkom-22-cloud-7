const asyncHandler = require('express-async-handler');
const User = require('../models/User');
const ErrorResponse = require('../utils/errorResponse');

// @desc    Impersonate user
// @route   POST /api/v1/auth/impersonate/:id
// @access  Private/Admin
exports.impersonate = asyncHandler(async (req, res, next) => {
  const user = await User.findById(req.params.id);

  if (!user) {
    return next(new ErrorResponse(`User not found with id of ${req.params.id}`, 404));
  }

  // Store original admin user ID in session
  if (!req.session.originalUser) {
    req.session.originalUser = req.user.id;
  }

  // Send back the user data to impersonate
  res.status(200).json({
    success: true,
    data: user
  });
});
