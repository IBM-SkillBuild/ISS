document.addEventListener('DOMContentLoaded', () => {
  const setNewTime = () => {
    const now = new Date();
    const launch = Date.parse("Fri, 20 Nov 1998 00:20:00 CST");
    const timeNow = now.getTime();
    const timeLeft = Math.abs(launch - timeNow);

    const days = Math.floor(timeLeft / 86400000);
    let remainingTime = timeLeft % 86400000;
    const hours = Math.floor(remainingTime / 3600000);
    remainingTime %= 3600000;
    const mins = Math.floor(remainingTime / 60000);
    remainingTime %= 60000;
    const secs = Math.floor(remainingTime / 1000);

    const formatNumber = (num) => num.toString().padStart(2, '0');

    const formattedTime = `${days} días ${formatNumber(hours)}:${formatNumber(mins)}:${formatNumber(secs)}`;
    document.getElementById("contador").textContent = formattedTime + " en orbita";
  };

  setNewTime();
  setInterval(setNewTime, 1000);
});