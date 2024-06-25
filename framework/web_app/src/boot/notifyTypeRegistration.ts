import { Notify } from 'quasar'

// See possible options: https://quasar.dev/quasar-plugins/notify/

Notify.setDefaults({

})

Notify.registerType('info', {
    color: 'blue',
    textColor: 'white',
    message: 'Hey did you know...',
    caption: "I'm a notification!",
    icon: 'announcement',
    iconColor: 'amber',
    iconSize: '30px',
    progress: true,
    classes: 'flat'
})

Notify.registerType('oopsie', {
    color: 'red-5',
    message: 'Oops, something went wrong...',
    icon: 'error',
    iconColor: 'white',
    iconSize: '30px',
    progress: true,
    timeout: 3000
})
