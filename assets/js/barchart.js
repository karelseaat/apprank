// Bar chart

var blaat = JSON.parse(document.getElementById("klont").getAttribute('names'));

function settings(set)
{

  console.log(JSON.parse(document.getElementById("labels-" + set).innerHTML),)

  return {
    type: 'bar',
    data: {
      labels: JSON.parse(document.getElementById("labels-" + set).innerHTML),
      datasets: [
        {
          // label: "Population (millions)",
          backgroundColor: ["#3e95cd", "#8e5ea2", "#3cba9f", "#e8c3b9", "#c45850", "#3e95cd", "#8e5ea2", "#3cba9f", "#e8c3b9", "#3cba9f"],
          data: JSON.parse(document.getElementById("data-" + set).innerHTML)
        }
      ]
    },
    options: {
      legend: { display: false },
      title: {
        display: true,
        text: document.getElementById("unit-" + set).innerHTML
      }
    }
  }
}

blaat.forEach(element => new Chart(document.getElementById(element + "-canvas"), settings(element)));
