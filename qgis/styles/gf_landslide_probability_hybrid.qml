<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34" styleCategories="Symbology">
  <pipe>
    <provider>
      <resampling zoomedInResamplingMethod="nearestNeighbour" zoomedOutResamplingMethod="nearestNeighbour" maxOversampling="2" enabled="false"/>
    </provider>
    <rasterrenderer type="singlebandpseudocolor" opacity="0.6" band="1" alphaBand="-1" classificationMin="0" classificationMax="0.21" nodataColor="">
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" classificationMode="1" clip="0" labelPrecision="4" minimumValue="0" maximumValue="0.21">
          <item value="0" color="#6285c4" label="0 (blue = less susceptible)" alpha="255"/>
          <item value="0.005" color="#6285c4" label="&lt;0.5%" alpha="255"/>
          <item value="0.007" color="#66bd63" label="0.7%" alpha="255"/>
          <item value="0.025" color="#a6d96a" label="2.5%" alpha="255"/>
          <item value="0.04" color="#ffe14d" label="4%" alpha="255"/>
          <item value="0.07" color="#fdae61" label="7%" alpha="255"/>
          <item value="0.12" color="#f46d43" label="12%" alpha="255"/>
          <item value="0.18" color="#d73027" label="18%" alpha="255"/>
          <item value="0.21" color="#a50026" label="21%" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0" gamma="1"/>
    <huesaturation saturation="0" grayscaleMode="0" colorizeOn="0" colorizeRed="255" colorizeGreen="128" colorizeBlue="128" colorizeStrength="100" invertColors="0"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
