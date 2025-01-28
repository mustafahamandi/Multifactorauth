const header = document.querySelector("h1");

setTimeout(() => {
    header.classList.add("finished");
}, 2000); // نفس مدة حركة الكتابة (2s)



    // تحديد جميع أيقونات تغيير كلمة المرور
const togglePasswordIcons = document.querySelectorAll('.toggle-password');

togglePasswordIcons.forEach((icon) => {
icon.addEventListener('click', () => {
    // تحديد حقل الإدخال المقابل للأيقونة
    const passwordInput = icon.previousElementSibling;

    // تبديل نوع الإدخال بين "password" و "text"
    const type = passwordInput.type === 'password' ? 'text' : 'password';
    passwordInput.type = type;

    // تبديل أيقونة العين بين "fa-eye" و "fa-eye-slash"
    icon.classList.toggle('fa-eye-slash');
});
});


    // الجزء الخاص  بالتحويلات بين صفحات 
    const signUpButton = document.getElementById('signUp');
    const signInButton = document.getElementById('signIn');
    const container = document.getElementById('container');
    const themeToggle = document.getElementById('themeToggle');

    signUpButton.addEventListener('click', () => {
        container.classList.add("right-panel-active");
    });

    signInButton.addEventListener('click', () => {
        container.classList.remove("right-panel-active");
    });
   // الجزء الخاص ب تحويل اليلي والنهاري 
    let isDarkMode = false;

themeToggle.addEventListener('click', () => {
isDarkMode = !isDarkMode;

if (isDarkMode) {
    document.documentElement.style.setProperty('--bg-color', '#121212');
    document.documentElement.style.setProperty('--text-color', '#FFFFFF');
    document.documentElement.style.setProperty('--link-color', '#BB86FC');
    document.documentElement.style.setProperty('--button-bg', '#BB86FC');
    document.documentElement.style.setProperty('--button-text', '#000000');
    document.documentElement.style.setProperty('--form-bg', '#1E1E1E');
    document.documentElement.style.setProperty('--input-bg', '#333333');

    themeToggle.textContent = "🌙"; // رمز القمر
    themeToggle.classList.remove("light-mode");
    themeToggle.classList.add("dark-mode");
} else {
    document.documentElement.style.setProperty('--bg-color', '#f6f5f7');
    document.documentElement.style.setProperty('--text-color', '#333');
    document.documentElement.style.setProperty('--link-color', '#333');
    document.documentElement.style.setProperty('--button-bg', '#FF4B2B');
    document.documentElement.style.setProperty('--button-text', '#FFFFFF');
    document.documentElement.style.setProperty('--form-bg', '#FFFFFF');
    document.documentElement.style.setProperty('--input-bg', '#eee');

    themeToggle.textContent = "☀️"; // رمز الشمس
    themeToggle.classList.remove("dark-mode");
    themeToggle.classList.add("light-mode");
}
});