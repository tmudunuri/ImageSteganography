// Range Slider
var slider = document.getElementById("nbits");
var output = document.getElementById("bits");
output.innerHTML = slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
slider.oninput = function() {
  output.innerHTML = this.value;
}