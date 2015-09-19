SIZES := \
	stopwatch/static/stopwatch/vaeske360.jpg \
	stopwatch/static/stopwatch/vaeske720.jpg \
	stopwatch/static/stopwatch/vaeske1080.jpg \
	stopwatch/static/stopwatch/vaeske1440.jpg \
	stopwatch/static/stopwatch/vaeske640.jpg \
	stopwatch/static/stopwatch/vaeske1280.jpg \
	stopwatch/static/stopwatch/vaeske1920.jpg

QUAL360 :=
QUAL640 :=
QUAL720 :=
QUAL1080 := -quality 80
QUAL1280 := -quality 75
QUAL1440 := -quality 70
QUAL1920 := -quality 60
all: $(SIZES)
.PHONY: all
$(SIZES): stopwatch/static/stopwatch/vaeske%.jpg: stopwatch/static/stopwatch/vaeske3256.jpg
	nice convert -verbose $< -resize $*x$* $(QUAL$*) $@
