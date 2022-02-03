"use strict";

var randomChartData = function randomChartData(n) {
  var data = [];

  for (var i = 0; i < n; i++) {
    data.push(Math.round(Math.random() * 200));
  }

  return data;
};

var chartColors = {
  "default": {
    primary: '#00D1B2',
    info: '#209CEE',
    danger: '#FF3860'
  }
};

// console.log(document.getElementById('apps').innerHTML)
var canvas = document.getElementById('big-line-chart')

var data_array = JSON.parse(document.getElementById('apps').innerHTML)

var allvalues = [];
for(var key in data_array) {
    // allvalues.push(data_array[key])
    for(var thekey in data_array[key]['data']) {
      if (data_array[key]['data'][thekey]['y'] !== "null")
      {
        allvalues.push(data_array[key]['data'][thekey]['y'])
      }

    }
}

// console.log(allvalues)

// console.log(Math.min.apply(this, data_array))

var ctx = canvas.getContext('2d');
var newchart = new Chart(ctx, {
  type: 'line',
  data: {
    datasets: data_array,
    labels: JSON.parse(document.getElementById('labels').innerHTML)
  },
  options: {

    maintainAspectRatio: false,
    legend: {
      display: true
    },
    responsive: true,
    tooltips: {
      backgroundColor: '#f5f5f5',
      titleFontColor: '#333',
      bodyFontColor: '#666',
      bodySpacing: 4,
      xPadding: 12,
      mode: 'nearest',
      intersect: 0,
      position: 'nearest'
    },
    scales: {
      yAxes: [{

        scaleLabel: {
        display: true,
        labelString: 'store pos'
      },
        barPercentage: 1.6,
        gridLines: {
          drawBorder: false,
          color: 'rgba(29,140,248,0.0)',
          zeroLineColor: 'transparent'
        },
        ticks: {
          beginAtZero: true,
          reverse: true,
          padding: 20,
          fontColor: '#9a9a9a',
          min: Math.min.apply(this, allvalues) - 2,
          max: Math.max.apply(this, allvalues) + 2
        }
      }],
      xAxes: [{
        scaleLabel: {
        display: true,
        labelString: 'At date'
      },
        barPercentage: 1.6,
        gridLines: {
          drawBorder: false,
          color: 'rgba(225,78,202,0.1)',
          zeroLineColor: 'transparent'
        },
        ticks: {
          padding: 20,
          fontColor: '#9a9a9a'
        }
      }]
    }
  }
});

canvas.onclick = function(evt) {
    var activePoints = newchart.getElementsAtEvent(evt);
    console.log(activePoints)
    // => activePoints is an array of points on the canvas that are at the same position as the click event.
};
