(function(){"use strict";var a=this;a.define(["backbone","communicator","models/NavBarItemModel","hbs!tmpl/NavBarItem"],function(a,b,c,d){var e=a.Marionette.ItemView.extend({model:c,template:{type:"handlebars",template:d},tagName:"li",cursor:"pointer",events:{click:"itemClicked"},itemClicked:function(){b.mediator.trigger(this.model.get("eventToRaise"),this)}});return{NavBarItemView:e}})}).call(this);