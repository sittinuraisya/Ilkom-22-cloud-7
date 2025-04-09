const { eventId } = useParams();
const [name, setName] = useState("");

const handleCheckIn = async () => {
  await axios.post(`http://localhost:5000/api/checkin`, { name, eventId });
};