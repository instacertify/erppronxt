/* Login page only. Does not touch the password check or any other page. */
(function () {
	function paint() {
		var body = document.body;
		if (!body || body.getAttribute("data-path") !== "login" || body.querySelector(".ic-login-brand")) return;
		var panel = document.createElement("aside");
		panel.className = "ic-login-brand";
		panel.innerHTML =
			'<div class="ic-login-brand-top">' +
			'<img src="/assets/instacertify/images/instacertify_app_logo.png" alt="" width="44" height="44">' +
			'<span class="ic-login-word"><span>Insta</span>certify</span>' +
			"</div>" +
			'<div class="ic-login-copy">' +
			"<h1>Simplifying Certification. Accelerating Business.</h1>" +
			"<p>One intelligent workspace to manage customers, certifications, testing and business operations.</p>" +
			"</div>" +
			'<div class="ic-login-diagram" aria-hidden="true">' +
			'<svg viewBox="0 0 360 150" width="100%" height="150">' +
			'<path d="M70 78 H150 M210 78 H290 M180 48 V108" fill="none" stroke="rgba(255,255,255,0.45)" stroke-width="1.5"/>' +
			'<g fill="none" stroke="#fff" stroke-width="1.5">' +
			'<rect x="28" y="48" width="56" height="60" rx="10"/>' +
			'<path d="M40 68 h32 M40 80 h24 M40 92 h28"/>' +
			'<circle cx="180" cy="78" r="28"/>' +
			'<path d="M168 78 l8 8 16-18"/>' +
			'<rect x="276" y="48" width="56" height="60" rx="10"/>' +
			'<path d="M292 78 h24 M304 66 v24"/>' +
			"</g>" +
			"</svg>" +
			"</div>" +
			'<p class="ic-login-foot">Instacertify Labs Private Limited</p>';
		body.insertBefore(panel, body.firstChild);
		body.classList.add("ic-login-split");
		var heading = document.querySelector("section.for-login .page-card-head h4");
		var subtitle = document.querySelector("section.for-login .page-card-head .page-card-subtitle");
		if (heading && /sign in|log in/i.test(heading.textContent || "")) heading.textContent = "Welcome back";
		if (subtitle) subtitle.textContent = "Sign in to continue to your workspace.";
		var button = document.querySelector("section.for-login .btn-login");
		if (button && /continue|log in|sign in/i.test(button.textContent || "")) button.textContent = "Sign In";
	}
	if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", paint);
	else paint();
})();
