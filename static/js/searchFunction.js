function showRecommendation(){
    var x = document.getElementById("recommendations");
    x.classList.remove("hidden");
    // console.log("Title is : " , title);
    
    var request = new XMLHttpRequest()
    var link = "http://127.0.0.1:8000/search/?query=" + title;
    request.open('GET', link, true);
    request.onload = function() {
    // Begin accessing JSON data here
    }
}

