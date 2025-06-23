function changeBackground() {
    const destination = document.getElementById("destination").value;
    const banner = document.getElementById("trip-banner");

    const images = {
        cairo: "/static/images/bg_cairo.jpg",
        london: "/static/images/bg_london.jpg",
        paris: "/static/images/bg_paris.jpg",
        tokyo: "/static/images/bg_tokyo.jpg",
        nyc: "/static/images/bg_nyc.jpg"
    };

    if (destination && images[destination]) {
        banner.style.backgroundImage = `url('${images[destination]}')`;
    } else {
        banner.style.backgroundImage = ""; // fallback
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const banner = document.getElementById("trip-banner");
    const destination = "{{ trip.destination|lower }}";
    const bgMap = {
        "paris": "/static/trips/images/bg_paris.jpg",
        "london": "/static/trips/images/bg_london.jpg",
        "tokyo": "/static/trips/images/bg_tokyo.jpg",
        "cairo": "/static/trips/images/bg_cairo.jpg",
        "nyc": "/static/trips/images/bg_nyc.jpg"
    };
    if (bgMap[destination]) {
        banner.style.backgroundImage = `url('${bgMap[destination]}')`;
    }
});

