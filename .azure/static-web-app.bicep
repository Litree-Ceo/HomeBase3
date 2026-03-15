// Bicep script for Azure Static Web App
param location string = resourceGroup().location
param appName string = 'homebase3-static'

resource staticWebApp 'Microsoft.Web/staticSites@2022-03-01' = {
  name: appName
  location: location
  properties: {
    repositoryUrl: ''
    branch: 'main'
    buildProperties: {
      appLocation: '/frontend'
      apiLocation: '/backend'
      outputLocation: 'dist'
    }
  }
}

