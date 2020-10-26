$('.airplane').draggable({
    axis: 'x',
    containment: "parent",
    move(event) {
        console.log(event.pageX,
            event.pageY)
    }
});
let level = 0;
speedCreating = 4;
speedScrolling = 2;
spacesBetween = 4;

function levelUp() {
    if (level == 1) {
        speedCreating = 3;
        speedScrolling = 2;
        spacesBetween = 3.5;
    }
    if (level == 2) {
        speedCreating = 3;
        speedScrolling = 2;
        spacesBetween = 3;
    }
    if (level == 3) {
        speedCreating = 3;
        speedScrolling = 1.5;
        spacesBetween = 3;
    }
    if (level == 4) {
        speedCreating = 3;
        speedScrolling = 1;
        spacesBetween = 3;
    }
    if (level == 5) {
        speedCreating = 2;
        speedScrolling = 1;
        spacesBetween = 3;
    }
    if (level == 6) {
        speedCreating = 2;
        speedScrolling = 0.5;
        spacesBetween = 3;
    }
    if (level == 7) {
        speedCreating = 2;
        speedScrolling = 0.5;
        spacesBetween = 2.5;
    }
    if (level == 8) {
        speedCreating = 2;
        speedScrolling = 0.5;
        spacesBetween = 2;
    }
}

let startGame;
let playing = true;

function createObjects() {
    startGame = setInterval(function() {
        // if (playing) {
        // Generuoja naujas judancias juostas
        firstWidthRandom = Math.floor(Math.random() * 80);
        SecondWidth = 100 - firstWidthRandom - spacesBetween * 10;
        $('.gameBox').append(`<div class="platform"style='left:0; width:${firstWidthRandom}%;'></div>`);
        $('.gameBox').append(`<div class="platform" style='right:0; width:${SecondWidth}%;'></div>`);
        // Trina juostas kuriu jau nesimato
        objectsWay = document.querySelectorAll('.platform');
        for (let i = 0; i < objectsWay.length; i++) {
            if (objectsWay[i].offsetTop > window.innerHeight) { objectsWay[i].remove(); }
        }
        // Animuoja juostas
        $('.platform').animate({
            marginTop: `+=${window.innerHeight}`,
        }, speedCreating * 1000, 'linear');
        // Perraso rezultata
        let currentScore = $('.timeScore').text();
        currentScore++;
        levelNew = Math.floor(currentScore / 50);
        $('.timeScore').text(currentScore);
        // End
        // playing = false;
        if (levelNew > 7) { levelNew = 7; }
        if (levelNew > level) {
            // Perraso esama leveli.
            level = levelNew;
            $('.level').text(level);
            // Sustabdo zaidima.
            clearInterval(startGame);
            // Istrinamos dar matomos juostos
            for (let z = 0; z < objectsWay.length; z++) { objectsWay[z].remove(); }
            $('.levelUp').css({ display: 'block' });
            $('.gameBox').css({ background: '#1a1919' });
            levelUp();
            // $('.platform').stop();
        }

    }, speedScrolling * 1000);
}
createObjects();
// event perejimui i kita lygi.
document.querySelector('.levelUp').addEventListener('click', function() {
    $('.levelUp').css({ display: 'none' });
    $('.gameBox').css({ background: '#5f5e5e' });
    clearInterval(startGame);
    createObjects();
})

// event pradejimui naujo zaidimo.
document.querySelector('.gameOver').addEventListener('click', function() {
    $('.gameOver').css({ display: 'none' });
    $('.gameBox').css({ background: '#5f5e5e' });
    clearInterval(startGame);
    createObjects();
})

function checkLife() {
    objectsWay = document.querySelectorAll('.platform');
    airplaneWay = document.querySelector('.airplane');
    for (let i = 0; i < objectsWay.length; i++) {
        // ar yra tame paciame aukstyje kaip ir judanti juosta
        if (objectsWay[i].getBoundingClientRect().top > airplaneWay.getBoundingClientRect().top) {
            // ar lektuvo apacia neliecia juostos kuria galbut dar nedingo...
            if (objectsWay[i].getBoundingClientRect().top < window.innerHeight - 10) {
                //ar liecia savo kaires puses savo kairiu sonu.
                if (objectsWay[i].getBoundingClientRect().left + objectsWay[i].getBoundingClientRect().width > airplaneWay.getBoundingClientRect().left) {
                    //ar liecia desinio sono savo desiniu sonu.
                    if (objectsWay[i].getBoundingClientRect().left < airplaneWay.getBoundingClientRect().left + airplaneWay.getBoundingClientRect().width) {
                        for (let z = 0; z < objectsWay.length; z++) { objectsWay[z].remove(); }
                        //Game over
                        $('.timeScore').text(0);
                        level = 0;
                        $('.level').text(0);
                        clearInterval(startGame);
                        $('.gameOver').css({ display: 'block' });
                        $('.gameBox').css({ background: '#1a1919' });

                    }
                }
            }
        }
    }
}
setInterval(checkLife, 100);