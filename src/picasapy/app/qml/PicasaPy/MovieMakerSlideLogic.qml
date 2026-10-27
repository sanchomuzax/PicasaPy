import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

QtObject {
    id: root
    required property var movieDialog
    required property var tabs

function addTextSlide(slide) {
    var slides = movieDialog.movieSlides.slice(0)
    var selected = movieDialog.movieSlideSelection.length
            ? movieDialog.movieSlideSelection : (tabs.movieSlideList.currentIndex >= 0
                ? [tabs.movieSlideList.currentIndex] : [])
    var insertionIndex = selected.length
            ? Math.max.apply(null, selected) + 1 : slides.length
    slides.splice(insertionIndex, 0, slide || {
        text: tabs.movieSlideText.text || qsTr("Text"),
        font: tabs.movieFontBox.currentText,
        size: movieDialog.textSizes[tabs.movieTextSizeBox.currentIndex],
        style: tabs.movieTextStyleBox.currentIndex,
        bold: tabs.movieBoldBox.checked,
        italic: tabs.movieItalicBox.checked,
        outline: tabs.movieOutlineBox.checked,
        textColor: movieDialog.textColor,
        backgroundColor: movieDialog.backgroundColor,
    })
    movieDialog.movieSlides = slides
    movieDialog.movieSlideSelection = [insertionIndex]
    movieDialog.movieSlideEditingIndex = insertionIndex
    tabs.movieSlideList.currentIndex = insertionIndex
    tabs.movieClipList.currentIndex = movieDialog.movieClipSources.length + insertionIndex
    loadTextSlide()
}
function loadTextSlide() {
    movieDialog.loadingTextSlide = true
    var index = tabs.movieSlideList.currentIndex
    var slide = index >= 0 && index < movieDialog.movieSlides.length
            ? movieDialog.movieSlides[index] : null
    if (slide) {
        tabs.movieSlideText.text = slide.text || qsTr("Text")
        var fontIndex = tabs.movieFontBox.model.indexOf(slide.font)
        if (fontIndex >= 0) tabs.movieFontBox.currentIndex = fontIndex
        var sizeIndex = movieDialog.textSizes.indexOf(slide.size)
        if (sizeIndex >= 0) tabs.movieTextSizeBox.currentIndex = sizeIndex
        tabs.movieTextStyleBox.currentIndex = Math.max(
            0, Math.min(11, slide.style || 0))
        tabs.movieBoldBox.checked = !!slide.bold
        tabs.movieItalicBox.checked = !!slide.italic
        tabs.movieOutlineBox.checked = !!slide.outline
        movieDialog.textColor = slide.textColor || "#ffffff"
        movieDialog.backgroundColor = slide.backgroundColor || "#000000"
    } else {
        tabs.movieSlideText.text = qsTr("Text")
        tabs.movieFontBox.currentIndex = tabs.movieFontBox.model.length > 0 ? 0 : -1
        tabs.movieTextSizeBox.currentIndex = 4
        tabs.movieTextStyleBox.currentIndex = 0
        tabs.movieBoldBox.checked = false
        tabs.movieItalicBox.checked = false
        tabs.movieOutlineBox.checked = false
        movieDialog.textColor = "#ffffff"
        movieDialog.backgroundColor = "#000000"
    }
    movieDialog.loadingTextSlide = false
}
function updateSelectedTextSlide() {
    var index = tabs.movieSlideList.currentIndex
    if (movieDialog.loadingTextSlide || index < 0 || index >= movieDialog.movieSlides.length)
        return
    var slides = movieDialog.movieSlides.slice(0)
    slides[index] = {
        text: tabs.movieSlideText.text || qsTr("Text"),
        font: tabs.movieFontBox.currentText || movieDialog.movieSlides[index].font
            || "DejaVuSans",
        size: tabs.movieTextSizeBox.currentIndex >= 0
            ? movieDialog.textSizes[tabs.movieTextSizeBox.currentIndex]
            : movieDialog.movieSlides[index].size || 16,
        style: tabs.movieTextStyleBox.currentIndex >= 0
            ? tabs.movieTextStyleBox.currentIndex
            : movieDialog.movieSlides[index].style || 0,
        bold: tabs.movieBoldBox.checked,
        italic: tabs.movieItalicBox.checked,
        outline: tabs.movieOutlineBox.checked,
        textColor: movieDialog.textColor.toString(),
        backgroundColor: movieDialog.backgroundColor.toString(),
    }
    movieDialog.movieSlides = slides
    tabs.movieSlideList.currentIndex = index
    tabs.movieClipList.currentIndex = movieDialog.movieClipSources.length + index
}
function removeTextSlide() {
    var selected = movieDialog.movieSlideSelection.length
            ? movieDialog.movieSlideSelection.slice(0)
            : (tabs.movieSlideList.currentIndex >= 0
                ? [tabs.movieSlideList.currentIndex] : [])
    if (!selected.length) return
    var slides = movieDialog.movieSlides.slice(0)
    selected.sort(function(a, b) { return b - a })
    selected.forEach(function(index) { slides.splice(index, 1) })
    movieDialog.movieSlides = slides
    var nextIndex = Math.min(selected[selected.length - 1], slides.length - 1)
    movieDialog.movieSlideSelection = nextIndex >= 0 ? [nextIndex] : []
    movieDialog.movieSlideEditingIndex = -1
    tabs.movieSlideList.currentIndex = nextIndex
    tabs.movieClipList.currentIndex = nextIndex >= 0
            ? movieDialog.movieClipSources.length + nextIndex
            : Math.min(tabs.movieClipList.currentIndex, movieDialog.movieClipSources.length - 1)
    loadTextSlide()
}
function selectTextSlide(index, modifiers) {
    var selected = movieDialog.movieSlideSelection.slice(0)
    if (modifiers & Qt.ControlModifier) {
        var at = selected.indexOf(index)
        if (at >= 0) selected.splice(at, 1)
        else selected.push(index)
    } else if (selected.indexOf(index) < 0) {
        selected = [index]
    }
    movieDialog.movieSlideSelection = selected
    tabs.movieSlideList.currentIndex = index
}
function moveTextSlides(targetIndex) {
    var selected = movieDialog.movieSlideSelection.length
            ? movieDialog.movieSlideSelection.slice(0) : [tabs.movieSlideList.currentIndex]
    selected = selected.filter(function(index) {
        return index >= 0 && index < movieDialog.movieSlides.length
    }).sort(function(a, b) { return a - b })
    if (!selected.length) return
    if (selected.indexOf(targetIndex) >= 0) return
    var slides = movieDialog.movieSlides.slice(0)
    var moving = selected.map(function(index) { return slides[index] })
    var removedBeforeTarget = selected.filter(function(index) {
        return index < targetIndex
    }).length
    var movingBeforeTarget = selected[selected.length - 1] < targetIndex
    for (var i = selected.length - 1; i >= 0; --i)
        slides.splice(selected[i], 1)
    var insertionIndex = Math.max(0, Math.min(
        slides.length,
        targetIndex - removedBeforeTarget + (movingBeforeTarget ? 1 : 0)))
    slides.splice.apply(slides, [insertionIndex, 0].concat(moving))
    movieDialog.movieSlides = slides
    movieDialog.movieSlideSelection = moving.map(function(_slide, index) {
        return insertionIndex + index
    })
    movieDialog.movieSlideEditingIndex = -1
    tabs.movieSlideList.currentIndex = insertionIndex
    tabs.movieClipList.currentIndex = movieDialog.movieClipSources.length + insertionIndex
}
function editTextSlide(index) {
    if (index < 0 || index >= movieDialog.movieSlides.length) return
    movieDialog.movieSlideSelection = [index]
    movieDialog.movieSlideEditingIndex = index
    tabs.movieSlideList.currentIndex = index
    loadTextSlide()
}
function updateSelectedText(text) {
    var index = movieDialog.movieSlideEditingIndex
    if (index < 0 || index >= movieDialog.movieSlides.length) return
    var slides = movieDialog.movieSlides.slice(0)
    var slide = Object.assign({}, slides[index])
    slide.text = text
    slides[index] = slide
    movieDialog.movieSlides = slides
    tabs.movieClipList.currentIndex = movieDialog.movieClipSources.length + index
}
}
