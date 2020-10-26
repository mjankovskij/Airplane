$('.airplane').draggable({
    axis: 'x',
    containment: "parent"
});

speed = 2; // bigger is lower
spacesBetween = 5; // 3 norm

function createObjects() {
    firstWidthRandom = Math.floor(Math.random() * 80);
    SecondWidth = 100 - firstWidthRandom - 20;
    let currentScore = document.querySelector('.timeScore').textContent;
    $('.gameBox').append(`<div class="platform" style='left:0; width:${firstWidthRandom}%;'></div>`);
    $('.gameBox').append(`<div class="platform" style='right:0; width:${SecondWidth}%;'></div>`);
    objectsWay = document.querySelectorAll('.platform');
    for (let i = 0; i < objectsWay.length; i++) {
        $('.platform').animate({
            marginTop: `+=${spacesBetween*100}`,
        }, speed * 1000, 'linear');
        if (objectsWay[i].offsetTop > window.innerHeight) {
            objectsWay[i].remove();
        }
    }
    setTimeout(createObjects, speed * 1000);
    currentScore = Number(currentScore) + 1;
    document.querySelector('.timeScore').innerHTML = currentScore;
}
createObjects();


function checkLife() {
    objectsWay = document.querySelectorAll('.platform');
    airplaneWay = document.querySelector('.airplane');
    for (let i = 0; i < objectsWay.length; i++) {
        if (objectsWay[i].getBoundingClientRect().top > airplaneWay.getBoundingClientRect().top) {
            if (objectsWay[i].getBoundingClientRect().top < window.innerHeight - 10) {
                if (objectsWay[i].getBoundingClientRect().left + objectsWay[i].getBoundingClientRect().width > airplaneWay.getBoundingClientRect().left) {
                    if (objectsWay[i].getBoundingClientRect().left < airplaneWay.getBoundingClientRect().left) {
                        (function(w) { w = w || window; var i = w.setInterval(function() {}, 100000); while (i >= 0) { w.clearInterval(i--); } })( /*window*/ );

                    }
                }
            }
            // console.log(objectsWay[i].getBoundingClientRect().top, airplaneWay.getBoundingClientRect().top)
            // console.log(objectsWay[i].getBoundingClientRect().left, airplaneWay.getBoundingClientRect().left)
        }
    }
}
setInterval(checkLife, 100);