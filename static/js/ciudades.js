document.addEventListener('DOMContentLoaded', () => {
  if (screen.width < 1200) {
    document.getElementsByClassName('slider-container').style.display="none"


  }
    
  const ciudades = {
    'SA': {center: [-63, -24], zoom: 2.4},
    'NA': {center: [-87, 41], zoom: 2.4},
    'dublin': {center: [-6.26, 53.34], zoom: 6.2},
    'mallorca': {center: [2.88, 39.6], zoom: 7.2},
    'caracas': {center: [-66.91, 10.50], zoom: 5.0},
    'paris': {center: [2.32, 48.8], zoom: 5.1},
    'huelva': {center: [-6.94, 37.2], zoom: 7.9},
    'madrid': {center: [-3.68, 40.47], zoom: 4.1},
    'vancouver': {center: [-123.11, 49.26], zoom: 5.6},
    'habana': {center: [-80.8395, 23.01], zoom: 5.1},
    'trinidad': {center: [-61.26, 10.44], zoom: 7.1},
    'londres': {center: [0.14, 51.4], zoom: 5.4}
  };

  const esDispositivoMovil = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

  function moverMapa(id) {
    if (screen.width < 1200) {
      document.getElementById('cerrar-aside').click();
    }

    const { center, zoom } = ciudades[id];

    if (esDispositivoMovil) {
      map.jumpTo({ center, zoom });
      setTimeout(() => map.fire('moveend'), 500);
    } else {
      map.flyTo({ center, zoom, speed: 0.2 });
    }
  }

  Object.keys(ciudades).forEach(id => {
    document.getElementById(id).addEventListener('click', () => moverMapa(id));
  });
});