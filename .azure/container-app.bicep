// Bicep script for Azure Container App
param location string = resourceGroup().location
param appName string = 'homebase3-api'
param image string = 'REPLACE_WITH_ACR_IMAGE_URL'

resource containerApp 'Microsoft.App/containerApps@2022-01-01-preview' = {
  name: appName
  location: location
  properties: {
    kubeEnvironmentId: ''
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
      secrets: []
    }
    template: {
      containers: [
        {
          name: appName
          image: image
          resources: {
            cpu: 0.5
            memory: '1Gi'
          }
        }
      ]
    }
  }
}

