var margin = {top: 30, right: 30, bottom: 10, left: 40},
    width = 960 - margin.left - margin.right,
    height = 200 - margin.top - margin.bottom,
    barheight = 100; //this is the height of the sentiment bar graph

var gmargin = {top: 50, right: 0, bottom: 50, left: 20},
    w = 960 - gmargin.left - gmargin.right,
    h = 500 - gmargin.top - gmargin.bottom,
    r1 = h / 2,
    r0 = r1 - 80;

var pos_color = "#f17d1d",
    neg_color = "#119191",
    node_color = "#045a8d",
    link_color = "#74a9cf";

var high_opacity = 0.9;
    low_opacity = 0.2;

//specity length of x axis
var x = d3.scale.linear()
    .range([10, width]);

//specify length of y axis
var y = d3.scale.linear()
    .range([0, barheight])
    .domain([0, 1]);

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

var sentiment_graph = d3.select("#sentiment").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("class", "sentgraph")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var chord = d3.layout.chord()
    .padding(.04)
    .sortSubgroups(d3.descending)
    .sortChords(d3.descending);

var arc = d3.svg.arc()
    .innerRadius(r0)
    .outerRadius(r0 + 20);

var nodes;

//add yaxis label
sentiment_graph.append("g")
    .attr("class", "y axis")
    .attr("id", "yaxis")
    .attr("visibility", "hidden")
    .append("text")
    .attr("transform", "rotate(-90), translate(0, -10)")
    // .attr("font-family", "sans-serif")
    .attr("font-size", "12px") 
    .style("text-anchor", "end")
    .text("")
    .append("svg:tspan").style("fill", neg_color).text("Negative ")
    .append("svg:tspan").style("fill", "black").text('\u2194')
    .append("svg:tspan").style("fill", pos_color).text(" Positive");

  var brush = d3.svg.brush()
    .x(x)
    .extent([0, 1])
    .on("brush", brushed)
    .on("brushend", brushend);

  var brushg = sentiment_graph.append("g")
      .attr("class", "brush")
      .call(brush);

  brushg.selectAll("rect")
      .attr("height", barheight+margin.top);
  brushg = d3.selectAll('.brush')
    .attr("visibility", "hidden")
    .selectAll(".resize")
    .append("path")
    .attr("id", "brushhandle")
    .attr("d", resizePath);

  $().ready(function() {
    $('#bookTitle').tipsy({
        fade: true,
        gravity: 's', 
        html: true, 
        title: function() {return "<span style='font-size:14px;'>Click to edit title</span>"}
    })
    $('#selectbook_button').tipsy({ 
        fade: true,
        gravity: 's', 
        html: true, 
        title: function() { return "<span style='font-size:14px;'>Select a visualization from the database</span>";}
      });
    $('#uploadbook_button').tipsy({ 
        fade: true,
        gravity: 's', 
        html: true, 
        title: function() { return "<span style='font-size:14px;'>Upload a text file to create a new visualization</span>";}
      });
    $('#editchars_button').tipsy({ 
        fade: true,
        gravity: 's', 
        html: true, 
        title: function() { return "<span style='font-size:14px;'>Edit characters tracked in the text</span>";}
      });
    $('#saveviz_button').tipsy({ 
        fade: true,
        gravity: 's', 
        html: true, 
        title: function() { return "<span style='font-size:14px;'>Save this visualization to the database</span>";}
      });
    $('#exportdata_button').tipsy({ 
        fade: true,
        gravity: 's', 
        html: true, 
        title: function() { return "<span style='font-size:14px;'>Export visualization data in JSON format</span>";}
      });
  });

  function resizePath(d) {
        var e = +(d == "e"),
            x = e ? 1.5 : -1.5,
            y = barheight /2 - margin.top / 2;
        return "M" + (.5 * x) + "," + y
            + "A6,6 0 0 " + e + " " + (6.5 * x) + "," + (y + 6)
            + "V" + (2 * y - 6)
            + "A6,6 0 0 " + e + " " + (.5 * x) + "," + (2 * y)
            + "Z"
            + "M" + (2.5 * x) + "," + (y + 8)
            + "V" + (2 * y - 8)
            + "M" + (4.5 * x) + "," + (y + 8)
            + "V" + (2 * y - 8);
  }
function brushed() {
  var extent0 = brush.extent(),
      extent1;
    var d0 = Math.round(extent0[0]),
        d1 = Math.round(extent0[1]);
    extent1 = [d0, d1];
  d3.select(this).call(brush.extent(extent1));
}

function brushend() {
  var extent = brush.extent()
  updateLinks(extent);
  d3.selectAll(".bar")
    .classed("selected", function(d, i) { if (extent[0] <= i && extent[1] > i) { return true } else { return false };})
}

function updateSentiment(data, senttext) {
    d3.selectAll('#yaxis').attr("visibility", "visible");
    x.domain([0, data.length]);

    var bar = d3.selectAll('.brush').selectAll(".bar")
            .data(data);

    // new data:
    bar.enter().insert("rect", ".resize")
       .attr("id", "bar")
       .attr("class", "bar")
       .attr("x", function(d, i) { return x(i); })
       .attr("y", function(d) { if (+d > 0)
        {return barheight*.5 - y(d)}
        else {return barheight*.5} })
        .attr("height",function(d) {if (+d > 0)
        {return y(d)}
        else {return Math.abs(y(d))} })
       .attr("width", width / data.length)
       .attr("class", function(d) { return +d < 0 ? "bar negative selected" : "bar positive selected"; });

    // removed data:
    bar.exit().remove();
    // updated data:
    bar
       .transition()
       .duration(250)
          .attr("y", function(d) {
              if (+d > 0)
                {return barheight*.5 - y(d)}
              else {return barheight*.5} })
          .attr("height",function(d) {
              if (+d > 0)
                {return y(d)}
              else {return Math.abs(y(d))} })
          .attr("x", function(d, i) { return x(i); })
          .attr("width", width / data.length)
          .attr("class", function(d) { return +d < 0 ? "bar negative selected" : "bar positive selected"; })
          .attr("sentence", function(d, i) { return senttext[i]; });


  $('.bar').tipsy({ 
        fade: true,
        gravity: 's', 
        html: true, 
        title: function() {
          var d = this.getAttribute('sentence');
          return '<span>' + d + '</span>'; 
        }
      });

  console.log('updating sentiment');
};

function updateVisualization(nodes, links) {
  d3.selectAll('.brush')
    .attr("visibility", "visible");

  $('#yaxis').tipsy({
        fade: true,
        gravity: 's', 
        html: true,
        title: function() {return "<span style='font-size:14px;'>The sentiment of each sentence is classified on a scale from strongly negative to strongly positive</span>"}
    })

  
  $('#brushhandle').tipsy({
        fade: true,
        gravity: 's', 
        html: true,
        title: function() {return "<span style='font-size:14px;'>Drag handles to select a limited section of the text</span>"}
    })

  d3.selectAll('#editchars_div')
    .style("visibility", "visible");

  d3.selectAll('#saveviz_div')
    .style("visibility", "visible");

  d3.selectAll('#exportdata_div')
    .style("visibility", "visible");

  var graph = document.getElementById('graph')
  if ( graph ) { graph.remove(); }

  var graph = d3.select("#visualization").append("svg:svg")
    .attr("id", "graph")
    .attr("width", w + gmargin.left + gmargin.right)
    .attr("height", h + gmargin.top + gmargin.bottom)
  .append("svg:g")
    .attr("transform", "translate(" + (w / 2 + gmargin.left + gmargin.right) + "," + (h / 2 + gmargin.top) + ")");

  if ( Object.keys(links).length > 0 ) {

    var matrix = [],
        n = nodes.length;

    var matrix = new Array(n);
    for (var i = 0; i < n; i++) {
      matrix[i] = new Array(n);
      for (var ii = 0; ii < n; ii++) {
      matrix[i][ii] = 0;
      }
    }

    links.forEach(function(link) {
    matrix[link.source][link.target] += link.value;
    matrix[link.target][link.source] += link.value;
    nodes[link.source].count += link.value;
    nodes[link.target].count += link.value;
  });

    if (d3.sum(d3.max(matrix)) > 0) {

  chord.matrix(matrix);

  var g = graph.selectAll("g.group")
      .data(chord.groups)
    .enter().append("svg:g")
      .attr("class", "group")
      .attr("id", "charnode")
      .on("mouseover", fade(low_opacity, links))
      .on("mouseout", fade(high_opacity, links))
      .on("click", function(d, i) { clicked(d, nodes[i].occurrences)});

  g.append("svg:path")
      .attr("id", "charnodepath")
      .style("stroke", d3.rgb(node_color).darker().darker())
      .style("fill", node_color)
      .attr("d", arc);

  g.append("svg:text")
      .each(function(d) { d.angle = (d.startAngle + d.endAngle) / 2; })
      .attr("class", "nodetitle")
      .attr("dy", ".35em")
      .attr("text-anchor", function(d) { return d.angle > Math.PI ? "end" : null; })
      .attr("transform", function(d) {
        return "rotate(" + (d.angle * 180 / Math.PI - 90) + ")"
            + "translate(" + (r0 + 26) + ")"
            + (d.angle > Math.PI ? "rotate(180)" : "");
      })
      .text(function(d, i) { return nodes[i].name; });

  graph.selectAll("path.chord")
      .data(chord.chords)
    .enter().append("svg:path")
      .attr("class", "chord")
      .style("stroke", d3.rgb(link_color).darker().darker())
      .style("fill", link_color)
      .attr("d", d3.svg.chord().radius(r0-5))
      .on("mouseover", fadeNodes(low_opacity))
      .on("mouseout", fadeNodes(high_opacity));

    $(".chord").tipsy({ 
        fade: true,
        gravity: $.fn.tipsy.autoNS, 
        html: true, 
        title: function() {
          var d = this.__data__;
          return '<span>' + "Connections between " + nodes[d.source.index].name + " and " + nodes[d.target.index].name + '</span>'; 
        }
        });
    } else {
      noLinks(graph);
    };
    } else {
      noLinks(graph);
    };

    function fade(opacity, links) {
      return function(d, i) {
        graph.selectAll("#charnode")
          .filter( function(dd) { return d == dd; })
          .attr("font-size", function() { if (opacity == high_opacity) { return 12; } else { return 14;} });

        graph.selectAll("path.chord")
            .filter(function(dd) { return dd.source.index != i && dd.target.index != i; })
          .transition()
            .style("stroke-opacity", opacity)
            .style("fill-opacity", opacity);

      var linked_links = graph.selectAll("path.chord")
          .filter(function(dd) { return dd.source.index != i && dd.target.index != i;});

      graph.selectAll("#charnode")
          .filter( function(dd, ii) { var linked = 0; links.forEach(function(link) { if ( (link.source == ii && link.value > 0 && link.target == i) || (link.target == ii && link.value > 0 && link.source == i) || (i == ii) ) { linked++; } }); return linked == 0; })
          .transition()
          .style("fill-opacity", opacity);
  };

}

      $("#charnode").tipsy({ 
        fade: true,
        gravity: 's', 
        html: true, 
        title: function() {
          return "<span style='font-size:14px;'>Click on a character's name to highlight their appearances</span>"; 
        }
      });

  function noLinks(graph) {
      graph.append("svg:text")
      .text("No links");
  }

    function fadeNodes(opacity) {
      return function(d, i) {
        graph.selectAll("#charnode")
          .filter( function(dd, i) { return d.source.index != i && d.target.index != i; })
          .transition()
          .style("fill-opacity", opacity);

        graph.selectAll("path.chord")
            .filter(function(dd) { return dd != d; })
          .transition()
            .style("stroke-opacity", opacity)
            .style("fill-opacity", opacity);
  };
};

};

function updateLinks(extent) {
  var charwindow = document.getElementById('charwindow_menu').value;
  var hiered = $('ol.sortable').nestedSortable('toHierarchy', {startDepthCount: 0});
  var ohiered = outputHierarchy(hiered);
  var book_id = document.getElementById('visualization').getAttribute('book_id');
  $.ajax({
          type: 'POST',
          url: '/charlinks/'+book_id,
          data: JSON.stringify({extent: extent, charwindow: charwindow, nodes: nodes, hierarchy: ohiered}),
          contentType: 'application/json;charset=UTF-8',
          processData: false,
          dataType: 'json'
      }).done(function(data, textStatus, jqXHR){
          updateVisualization(data['nodes'], data['links']);
          if ($('#interactor').hasClass('active')) {
            $('#interactor').removeClass('active')
          }
      }).fail(function(data){
          alert('error!');
      });
  };

$("html").click(function(event) { 
    if(!$(event.target).closest('#charnode').length &&
       !$(event.target).is('#charnode') &&
       !$(event.target).closest('#sentiment').length &&
       !$(event.target).is('#sentiment') &&
       document.getElementById("graph")) {
        clickedOutside();
        }     
});

function clickedOutside() {
  d3.selectAll(".nodetitle")
      .transition()
      .duration(200)
      .attr("fill", "#000")
      .attr("font-size", 12);

d3.selectAll(".bar")
    .attr("stroke-opacity", 0)
    .transition()
    .duration(1000)
    .attr("fill-opacity", 0.8)
    .attr("stroke-opacity", 0);
};

function clicked(d, occurrences) {
    d3.selectAll(".bar")
        .attr("stroke", function(d, i) { if (d<0 && occurrences[i]) {return neg_color} else if (d>0 && occurrences[i]) {return pos_color};})
        .attr("fill-opacity", 0.8)
        .attr("stroke-opacity", 0)
        .transition()
        .duration(1000)
        .attr("fill-opacity", function(d, i) { if (occurrences[i]) { return 1} else { return 0.3}; })
        .attr("stroke-opacity", function(d, i) { if (occurrences[i]) { return 1} else { return 0}; });

    d3.selectAll(".nodetitle")
        .transition()
        .duration(1000)
        .attr("fill", function(dd, i) { if (d.index == i) {return pos_color;} else {return "#000";} })
        .attr("font-size", function(dd, i) { if (d.index == i) {return 14;} else {return 12;} })
};

function uploadpressed() {
  $('#charwindow_button').find('.btn').html('5 <span class="caret"></span>');
  $('#charwindow_button').find('.btn').val('5');
    event.preventDefault();
    var form_data = new FormData($('#uploadform')[0]);
    $.ajax({
        type: 'POST',
        url: '/uploadajax',
        data: form_data,
        contentType: false,
        processData: false,
        dataType: 'json'
    }).done(function(data, textStatus, jqXHR){
        console.log('File uploaded!');
        updateSentiment(data['sentiments'], data['sentences']);
        updateChars(data['book_id'],data['characters']);
        updateVisualization(data['nodes'], data['links']);
        nodes = data['nodes'];
        document.getElementById('bookTitle').innerText = data['title'];
        document.getElementById('visualization').setAttribute('book_id', data['book_id']);
        d3.selectAll('#charselector')
          .style("visibility", "visible");
        d3.selectAll('.bookTitle')
          .style("visibility", "visible");
        if (!($('#interactor').hasClass('active'))) {
            $('#interactor').addClass('active')
          }
    }).fail(function(data){
        alert('error!');
    });
};

$("[id^=select_book]").click(function() {
  $('#charwindow_button').find('.btn').html('5 <span class="caret"></span>');
  $('#charwindow_button').find('.btn').val('5');
  event.preventDefault();
  var book_id = $(this).attr('value');
  $.ajax({
        type: 'POST',
        url: '/select_book/'+book_id,
          contentType: false,
          processData: false,
          dataType: 'json'
  }).done(function(data, textStatus, jqXHR){
      updateSentiment(data['sentiments'], data['sentences']);
      updateChars(data['book_id'],data['characters']);
      updateVisualization(data['nodes'], data['links']);
      nodes = data['nodes']
      document.getElementById('bookTitle').innerText = data['title'];
      document.getElementById('visualization').setAttribute('book_id', data['book_id']);
      d3.selectAll('.bookTitle')
          .style("visibility", "visible");
      brush.extent([0, data['sentences'].length]);
      brush(d3.select(".brush").transition());
      d3.selectAll('#charselector')
          .style("visibility", "visible");
      if ($('#interactor').hasClass('active')) {
            $('#interactor').removeClass('active')
          }
  }).fail(function(data){
      alert('error!');
  })


});

$('#editchars_button').click(function () {
            if ($('#interactor').hasClass('active')) {
                $('#interactor').removeClass('active')
            } else {
                $('#interactor').addClass('active')
            }
            return false;
      });

$('#close_interactor').click(function () {
            if ($('#interactor').hasClass('active')) {
                $('#interactor').removeClass('active')
            } else {
                $('#interactor').addClass('active')
            }
            return false;
      });

$('#close_copyoutput').click(function () {
    $('#copyoutput').removeClass('active')
});

window.addEventListener("keydown", function(e) {
if (e.keyCode == 191)
  if ($('#about_modal').hasClass('active')) {
      $('#about_modal').removeClass('active')
  } else {
      $('#about_modal').addClass('active')
  }
  return false;
  });

$('#about_button').click(function () {
            if ($('#about_modal').hasClass('active')) {
                $('#about_modal').removeClass('active')
            } else {
                $('#about_modal').addClass('active')
            }
            return false;
});

$('#close_about').click(function () {
    $('#about_modal').removeClass('active')
});

$('#close_about_button').click(function () {
    $('#about_modal').removeClass('active')
});

$(".dropdown-menu.charwindow li a").click(function(){
  $('#charwindow_button').find('.btn').html($(this).text() + ' <span class="caret"></span>');
  $('#charwindow_button').find('.btn').val($(this).data('value'));
});

$('#exportdata_button').click(function() {
  event.preventDefault();
  var title = document.getElementById('bookTitle').innerText;
  var book_id = document.getElementById('visualization').getAttribute('book_id');
  $.ajax({
        type: 'POST',
        url: '/export/'+book_id,
        data: JSON.stringify({title: title}),
        contentType: 'application/json;charset=UTF-8',
        processData: false,
        dataType: 'json'
    }).done(function(data, textStatus, jqXHR){
        $('#copyoutput').addClass('active');
        var output = document.getElementById('outputtext');
        output.innerText = JSON.stringify(data);
        document.getElementById('copyjson').removeAttribute('disabled');
    }).fail(function(data){
        alert('error!');
    });
});

$('#copyjson').click(function() {
  var copyTextarea = document.getElementById('outputtext');
  copyTextarea.select();
  try {
    var successful = document.execCommand('copy');
    $('#copyoutput').removeClass('active');
    var msg = successful ? 'successful' : 'unsuccessful';
    console.log('Copying text command was ' + msg);
  } catch (err) {
    console.log('Oops, unable to copy');
  }
});

$('#saveviz_button').click(function() {
  var title = document.getElementById('bookTitle').innerText;
  var book_id = document.getElementById('visualization').getAttribute('book_id');
  $.ajax({
    type: 'POST',
    url: '/savetodb/'+book_id,
    data: JSON.stringify({title:title}),
    contentType: 'application/json;charset=UTF-8',
    processData: false,
    dataType: 'json'
  }).done(function(data, textStatus, jqXHR){
    var book_id = data['book_id'];
    var selector = document.getElementById('selectbook_dropdown');
    var bookli = document.createElement('li');
    var booka = document.createElement('a');
    var bookatext = document.createTextNode(title);
    booka.setAttribute("href", "#");
    booka.setAttribute("value", book_id);
    booka.setAttribute("id", "select_book"+book_id);
    booka.appendChild(bookatext);
    bookli.appendChild(booka);
    selector.appendChild(bookli);
    }).fail(function(data){
        alert('error!');
    });
});

$.fn.inlineEdit = function(replaceWith, connectWith) {

    $(this).hover(function() {
        $(this).addClass('hover');
    }, function() {
        $(this).removeClass('hover');
    });

    $(this).click(function() {

        var elem = $(this);

        elem.hide();
        elem.after(replaceWith);
        replaceWith.focus();

        replaceWith.blur(function() {

            if ($(this).val() != "") {
                connectWith.val($(this).val()).change();
                elem.text($(this).val());
            }

            $(this).remove();
            elem.show();
        });
    });

};

$().ready(function(){
  var replaceWith = $('<input name="temp" type="text" />'),
      connectWith = $('input[name="hiddenField"]');

  $('.bookTitle').inlineEdit(replaceWith, connectWith);

});

$().ready(function(){
  var ns = $('ol.sortable').nestedSortable({
    forcePlaceholderSize: true,
    handle: 'div',
    helper: 'clone',
    items: 'li',
    opacity: .6,
    placeholder: 'placeholder',
    revert: 250,
    tabSize: 25,
    tolerance: 'pointer',
    toleranceElement: '> div',
    maxLevels: 2,
    isTree: true,
    expandOnHover: 700,
    startCollapsed: false,
    change: function(){
      console.log('Relocated item');
    }
  });
  
  $('.deleteMenu').attr('title', 'Click to delete item.');
  $('.itemTitle').attr('title', 'Click to edit name.');
  $('.menuDiv').attr('title', 'Click to move item.');

  $('.disclose').on('click', function() {
    $(this).closest('li').toggleClass('mjs-nestedSortable-collapsed').toggleClass('mjs-nestedSortable-expanded');
    $(this).toggleClass('ui-icon-plusthick').toggleClass('ui-icon-minusthick');
  });
  
  $('.deleteMenu').on("click", function(){
    var id_str = $(this).attr('data-id');
    var id = +id_str.split('_')[1];
    deleteName(id);
  });

  $('.itemTitle').on("click", function() {
   var id = $(this).attr('data-id');
   editName(id);
  });

  $('#addChar').on("click", function() {
    var new_char = {'title': "New Character", 'names': ['New Character']};
    addCharacter(new_char, false);
  });

  $('#submit_chars').click(function(e){
    event.preventDefault();
    var hiered = $('ol.sortable').nestedSortable('toHierarchy', {startDepthCount: 0});
    var ohiered = outputHierarchy(hiered);
    var charwindow = document.getElementById('charwindow_menu').value;
    var extent = brush.extent();
    var book_id = document.getElementById('visualization').getAttribute('book_id');
    $.ajax({
            type: 'POST',
            url: '/charajax/'+book_id,
            data: JSON.stringify({hierarchy: ohiered, charwindow: charwindow, extent: extent}),
            contentType: 'application/json;charset=UTF-8',
            processData: false,
            dataType: 'json'
        }).done(function(data, textStatus, jqXHR){
            updateVisualization(data['nodes'], data['links']);
              if ($('#interactor').hasClass('active')) {
                $('#interactor').removeClass('active')
      }
        }).fail(function(data){
            alert('error!');
        });
  })

});

function addCharacter(character, end) {
    var characters = document.getElementById('characters');
    var alists = document.getElementsByClassName("mjs-nestedSortable-expanded");
    var blists = document.getElementsByClassName("mjs-nestedSortable-leaf");
    var newchar_id = alists.length+blists.length;
    while (document.getElementById("menuItem_"+newchar_id)) { newchar_id++; };

    var new_char=document.createElement("li");
    new_char.style="display: list-item;";
    new_char.className="mjs-nestedSortable-branch mjs-nestedSortable-expanded";
    new_char.id="menuItem_"+newchar_id;
    new_char.title='Click to move item.';

    var new_div=document.createElement("div");
    new_div.className="menuDiv";
    var new_label=document.createElement("label");
    new_label.className="itemTitle";
    new_label.setAttribute("data-id", newchar_id);
    new_label.textContent= character.title;
    new_label.title='Click to edit name.';
    new_label.onclick = function() { editName(newchar_id) };

    var new_input=document.createElement("input");
    new_input.type="text";
    new_input.className="edit-input";
    new_input.style="display:none;";
    var new_delete=document.createElement("span");
    new_delete.setAttribute("data-id", "delete_"+newchar_id);
    new_delete.className="deleteMenu ui-icon ui-icon-closethick red";
    new_delete.title='Click to delete item.';
    new_delete.onclick = function() { deleteName(newchar_id) };

    new_div.appendChild(new_label);
    new_div.appendChild(new_input);
    new_div.appendChild(new_delete);
    new_char.appendChild(new_div);
    if (end) {
      characters.appendChild(new_char);
    } else {
      characters.insertBefore( new_char, characters.firstChild );
    };
    if (character.names.length > 1) {
        for(j=0;j<character.names.length;j++) {
            var new_name_list=document.createElement("ol");
            if (character.names[j] != character.title){
                var alists = document.getElementsByClassName("mjs-nestedSortable-expanded");
                var blists = document.getElementsByClassName("mjs-nestedSortable-leaf");
                var newname_id = alists.length+blists.length;
                while (document.getElementById("menuItem_"+newname_id)) { newname_id++; };
                var new_name=document.createElement("li");
                    new_name.style="display: list-item;";
                    new_name.className="mjs-nestedSortable-branch mjs-nestedSortable-leaf";
                    new_name.id="menuItem_"+newname_id;
                    new_name.title='Click to move item.';
                    var new_div=document.createElement("div");
                    new_div.className="menuDiv";
                    var new_label=document.createElement("label");
                    new_label.className="itemTitle";
                    new_label.setAttribute("data-id", newname_id);
                    new_label.textContent= character.names[j];
                    new_label.title='Click to edit name.';
                    new_label.onclick = function() { editName(newname_id) };

                    var new_input=document.createElement("input");
                    new_input.type="text";
                    new_input.className="edit-input";
                    new_input.style="display:none;";
                    var new_delete=document.createElement("span");
                    new_delete.setAttribute("data-id", "delete_"+newname_id);
                    new_delete.className="deleteMenu ui-icon ui-icon-closethick red";
                    new_delete.title='Click to delete item.';
                    new_delete.onclick = function() { deleteName(newname_id) };

                    new_div.appendChild(new_label);
                    new_div.appendChild(new_input);
                    new_div.appendChild(new_delete);
                    new_name.appendChild(new_div);
                    new_name_list.appendChild(new_name);
            }
            new_char.appendChild(new_name_list);
        }
    }
    }
function deleteName(id) {
  var name = $("label[data-id="+id+"]").text().trim();
  $('#menuItem_'+id).remove();
  console.log("Removing " + id + ". " + name);
}

function editName(id) {
  // Based on: http://stackoverflow.com/questions/16792502/change-label-to-textbox-on-edit-hyperlink-click
  var inputname = $("label[data-id="+id+"]").text().trim();
  console.log("Editing name for " + id + ". " + inputname);
  var input = $('<input id="item-text" type="text" value="' + inputname + '" />')
  $("label[data-id="+id+"]").parent().append(input);
    $("label[data-id="+id+"]").hide();
  input.focus();
  input.select();

  input.blur(function() {
     var name = $('#item-text').val();
     if ( name == "" ) {
      name = "NONE";
     }
     $('#item-text').parent().find('.itemTitle').show();
     $('#item-text').parent().find('.itemTitle').text(name);
     $('#item-text').remove();
  });
}

function removeAllCharacters() {
  var characters = document.getElementById('characters');
  while (characters.firstChild) {
    characters.removeChild(characters.firstChild);
  }

}

function outputHierarchy(arr,level) {
  var char_array = [];
  if(!level) level = 0;
  var level_padding = "";
  for(var j=0;j<level+1;j++) level_padding += "    ";

  if(typeof(arr) == 'object') {
    for(var item in arr) {
      var value = arr[item];
      if(typeof(value) == 'object') {
        value.name = $("label[data-id="+value.id+"]").text().trim();
        var new_name = new Object;
        new_name.name = value.name;
        if(value.hasOwnProperty("children")) {
          new_name.children=outputHierarchy(value.children);
        }
        char_array.push(new_name);
      }
    }
  }
  return char_array;
}

function updateChars(book_id, characters) {
  console.log('Updating characters!');
  removeAllCharacters();
  for(var j=0;j<characters.length;j++) {
  addCharacter(characters[j], true);
  }
  var characters = document.getElementById('characters');
  characters.setAttribute('book_id', book_id);
}