SIZES := stopwatch/static/stopwatch/vaeske480.jpg stopwatch/static/stopwatch/vaeske960.jpg stopwatch/static/stopwatch/vaeske1440.jpg stopwatch/static/stopwatch/vaeske1920.jpg
all: $(SIZES)
.PHONY: all
$(SIZES): stopwatch/static/stopwatch/vaeske%.jpg: stopwatch/static/stopwatch/vaeske3256.jpg
	convert $< -resize $*x$* $@
