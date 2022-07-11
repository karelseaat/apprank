"use strict";

var canvas = document.getElementById('big-line-chart')

var data_array = JSON.parse(document.getElementById('apps').innerHTML)

var allvalues = [];
for(var key in data_array) {

    for(var thekey in data_array[key]['data']) {
      if (data_array[key]['data'][thekey]['y'] !== "null")
      {
        allvalues.push(data_array[key]['data'][thekey]['y'])
      }

    }
}


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
