const XLSX = require("xlsx");

router.get("/api/export/:eventId", async (req, res) => {
  const attendees = await Attendee.find({ eventId: req.params.eventId });
  const worksheet = XLSX.utils.json_to_sheet(attendees);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Peserta");
  const buffer = XLSX.write(workbook, { type: "buffer" });
  res.setHeader("Content-Disposition", "attachment; filename=peserta.xlsx");
  res.end(buffer);
});