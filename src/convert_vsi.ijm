
suffix = '.vsi';
zplane = 0;
// flattenFolders = true; // this flag controls output directory structure
currentDirectory = File.getParent(getDirectory("startup"));
grandparentDirectory = File.getParent(File.getParent(currentDirectory));
inputFolder = grandparentDirectory + '/Input Images/';
outputFolder = grandparentDirectory + '/Input Images/';

// suffixFile should be a basic .txt file that contains one of the following:
// .jpg
// .gif
// .tiff
// .png

// suffixFile = currentDirectory + '/suffix.txt';
// outputSuffix = File.openAsString(suffixFile);
outputSuffix = '.png' // substring(outputSuffix, 0, lengthOf(outputSuffix) - 1);

// print(grandparentDirectory);
// print(inputFolder);
list = getFileList(inputFolder);

for (i=0; i < list.length; i++) {
  if (endsWith(list[i], suffix)) {
    // print(list[i]);
    vsiFile = list[i];
    processFile(inputFolder, outputFolder, vsiFile);
  }
}

run("Quit");

function processFile(inFolder, outFolder, vsi) {
  // print("inFolder: " + inFolder);
  // print("outFolder: " + outFolder);
  // print("vsi: " + vsi);
  print('run bio-formats importer');

  run("Bio-Formats Importer", "open=[" + inFolder + vsi + "] autoscale color_mode=Custom specify_range split_channels view=Hyperstack stack_order=XYCZT series_1 c_begin_1=1 c_end_1=3 c_step_1=1 z_begin_1=zplane z_end_1=zplane z_step_1=0 series_0_channel_0_red=0 series_0_channel_0_green=0 series_0_channel_0_blue=255 series_0_channel_1_red=0 series_0_channel_1_green=255 series_0_channel_1_blue=0 series_0_channel_2_red=255 series_0_channel_2_green=0 series_0_channel_2_blue=0");

  print("Blue...");
  selectImage(1);
  title1 = getTitle();

  print("Green...");
  selectImage(2);
  title2 = getTitle();
  run("Enhance Contrast", "saturated=0.35");
  resetMinAndMax();

  print("Red...");
  selectImage(3);
  title3 = getTitle();

	print("Merging Channels...");
  // print("titles: " + title1 + " " + title2 + " " + title3);
	run("Merge Channels...", "red='" + title3 + "' green='" + title2 + "' blue='" + title1 + "' gray=*None* cyan=*None* magenta=*None* yellow=*None*");

	print("Saving " + outputSuffix);

	saveAs(substring(outputSuffix, 1), outFolder + vsi);

	print("Closing open files...");
	run("Close All");

	print("Collecting Garbage...");
	run("Collect Garbage");
}
