// Copyright (c) OpenAI. All rights reserved.
"use strict";

const layout = require("../layout");

module.exports = {
  inferElementType: layout.inferElementType,
  compareElementPosition: layout.compareElementPosition,
  warnIfSlideHasOverlaps: layout.warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds: layout.warnIfSlideElementsOutOfBounds,
  alignSlideElements: layout.alignSlideElements,
  distributeSlideElements: layout.distributeSlideElements,
  getSlideDimensions: layout.getSlideDimensions,
};
