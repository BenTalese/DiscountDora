export default class ImageService {
    decodeBase64Image = (encodedImage: string) => `data:image/jpeg;base64,${encodedImage}`;
}
