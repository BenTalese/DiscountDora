import { setCssVar } from 'quasar';

interface Theme {
    // Brand Colours
    primary: string;
    secondary: string;
    accent: string;

    // Background Colours
    'page-background': string;
    componentBackground: string;

    // Status Colours
    positive: string;
    negative: string;
    info: string;
    warning: string;

    // Element Colours
    text: string;
    disabled: string;
    border: string;
    divider: string;
    focus: string;
}

const themes: { [key: string]: Theme } = {
    doraLight: {
        primary: '#17B073',
        secondary: '#006A80',
        accent: '#FED224',
        'page-background': '#E8F6F3',
        componentBackground: '#FFFFFF',
        positive: '#8CF596',
        negative: '#FF9966',
        info: '#93C2C2',
        warning: '#EDE461',
        text: '#333333',
        disabled: '#BDBDBD',
        border: '#BDBDBD',
        divider: '#BDBDBD',
        focus: '#17B073'
    }
    // TODO: More themes!
};

export default class ThemeService {
    applyTheme = () => {
        // TODO: Get currently logged in user, get settings from User/Setting/OptionApiService or something
        Object.entries(themes['doraLight']!).forEach(([key, value]) => setCssVar(key, value));
    };
}
