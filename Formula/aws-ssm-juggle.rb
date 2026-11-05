class AwsSsmJuggle < Formula
  include Language::Python::Virtualenv

  desc "AWS SSM tool for ECS/EC2 (Shell, SSH/SCP, Port Forwarding, ...)"
  homepage "https://github.com/morph027/aws-ssm-juggle"
  url "https://files.pythonhosted.org/packages/9e/26/9d22e2ba9392f9b9926d383da89c533b4c99823319bd0a1bfc175c19b2cd/aws_ssm_juggle-26.10.1.tar.gz"
  sha256 "940f3753b0f02924841e5246d5a54870f728dab2a92140b622f7f5c5a14d759f"
  license "MIT"

  depends_on "python@3.14"

  resource "boto3" do
    url "https://files.pythonhosted.org/packages/fc/8a/64b46f075149f9160da44aa7e1052dd18431b9ad4435beb0cfb02cc48624/boto3-1.43.123.tar.gz"
    sha256 "055fabb990c5d2f31fce4ca569255bd640cdd11a3ca68c9ecad35f4f8a5b83b5"
  end

  resource "botocore" do
    url "https://files.pythonhosted.org/packages/e0/de/011fc2a47fb066c47064b122498d2fd21f55bc90ea514acbddc37ca0f8c1/botocore-1.43.123.tar.gz"
    sha256 "80948cb9b1cdf1a1a25809089a42e3a1bc4af0258d198222db6e97dcc660dd0c"
  end

  resource "configargparse" do
    url "https://files.pythonhosted.org/packages/bc/d9/c591a80cf3335de7820c6762f8ee9298a43da5319803d319e16657b6fdf2/configargparse-1.9.0.tar.gz"
    sha256 "48d9c22affe4ac419b4dd0691fa929d759e1f99574be41826785f2dbf3da63a5"
  end

  resource "diskcache" do
    url "https://files.pythonhosted.org/packages/3f/21/1c1ffc1a039ddcc459db43cc108658f32c57d271d7289a2794e401d0fdb6/diskcache-5.6.3.tar.gz"
    sha256 "2c3a3fa2743d8535d832ec61c2054a1641f41775aa7c556758a109941e33e4fc"
  end

  resource "inquirerpy" do
    url "https://files.pythonhosted.org/packages/64/73/7570847b9da026e07053da3bbe2ac7ea6cde6bb2cbd3c7a5a950fa0ae40b/InquirerPy-0.3.4.tar.gz"
    sha256 "89d2ada0111f337483cb41ae31073108b2ec1e618a49d7110b0d7ade89fc197e"
  end

  resource "jmespath" do
    url "https://files.pythonhosted.org/packages/d3/59/322338183ecda247fb5d1763a6cbe46eff7222eaeebafd9fa65d4bf5cb11/jmespath-1.1.0.tar.gz"
    sha256 "472c87d80f36026ae83c6ddd0f1d05d4e510134ed462851fd5f754c8c3cbb88d"
  end

  resource "munch" do
    url "https://files.pythonhosted.org/packages/e7/2b/45098135b5f9f13221820d90f9e0516e11a2a0f55012c13b081d202b782a/munch-4.0.0.tar.gz"
    sha256 "542cb151461263216a4e37c3fd9afc425feeaf38aaa3025cd2a981fadb422235"
  end

  resource "pfzy" do
    url "https://files.pythonhosted.org/packages/d9/5a/32b50c077c86bfccc7bed4881c5a2b823518f5450a30e639db5d3711952e/pfzy-0.3.4.tar.gz"
    sha256 "717ea765dd10b63618e7298b2d98efd819e0b30cd5905c9707223dceeb94b3f1"
  end

  resource "prompt-toolkit" do
    url "https://files.pythonhosted.org/packages/7d/ea/39b988c938f75cb75d7045b5c69f8bfed47ee2152c8837fb403de29d6fb8/prompt_toolkit-3.0.53.tar.gz"
    sha256 "9ec8a0ad96d5c56148b3f914aa79c1564c3fde5d2e6b876e7bc327e353cf8fa6"
  end

  resource "psutil" do
    url "https://files.pythonhosted.org/packages/aa/c6/d1ddf4abb55e93cebc4f2ed8b5d6dbad109ecb8d63748dd2b20ab5e57ebe/psutil-7.2.2.tar.gz"
    sha256 "0746f5f8d406af344fd547f1c8daa5f5c33dbc293bb8d6a16d80b4bb88f59372"
  end

  resource "python-dateutil" do
    url "https://files.pythonhosted.org/packages/66/c0/0c8b6ad9f17a802ee498c46e004a0eb49bc148f2fd230864601a86dcf6db/python-dateutil-2.9.0.post0.tar.gz"
    sha256 "37dd54208da7e1cd875388217d5e00ebd4179249f90fb72437e91a35459a0ad3"
  end

  resource "s3transfer" do
    url "https://files.pythonhosted.org/packages/49/c5/0a5ce655109cb96b8dfad36908a4e108d15f5dc2eff8fbc3146c4312e704/s3transfer-0.19.3.tar.gz"
    sha256 "8326acc3d056d7f7b8a37110c7d2aea41f67e83f6ae79cd3b5fbcca34c726406"
  end

  resource "shtab" do
    url "https://files.pythonhosted.org/packages/ff/dd/e58588cf2d02266d504f4399979740b8b2b61fbd7719a89578afaa6558a3/shtab-1.13.0.tar.gz"
    sha256 "0a5be9d7ab2b4549e9a38252abcd5ecf5ec6813ecd80c6b06fa851bff55a5085"
  end

  resource "six" do
    url "https://files.pythonhosted.org/packages/94/e7/b2c673351809dca68a0e064b6af791aa332cf192da575fd474ed7d6f16a2/six-1.17.0.tar.gz"
    sha256 "ff70335d468e7eb6ec65b95b99d3a2836546063f63acc5171de367e834932a81"
  end

  resource "urllib3" do
    url "https://files.pythonhosted.org/packages/e3/05/b17359e1cefb4f909b5e40b1b90a496d987258916dbbf88e842c729f510e/urllib3-2.8.0.tar.gz"
    sha256 "63bf2ead4c879426ebf22ef2a781eeb4aa3b4ae798a0435506f8687fd5bb9b63"
  end

  resource "wcwidth" do
    url "https://files.pythonhosted.org/packages/ea/01/e5ac23733628a6bbb91913a765fcf55ee8070d8d991bc88fdaaf805052c7/wcwidth-0.9.4.tar.gz"
    sha256 "fd8d57d3cdfe570e3265c8fab1885c24e34ef40889c0759c0c304a19e9835954"
  end

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      ec2-juggle and ecs-juggle require the AWS session-manager-plugin:
        macOS: brew install --cask session-manager-plugin
        Linux (package repo with updates, recommended): https://gitlab.com/packaging/aws-session-manager-plugin
        Linux (manual): https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html
    EOS
  end

  test do
    # the CLIs exit on import if session-manager-plugin is not on PATH, so provide a stub
    (testpath/"bin/session-manager-plugin").write <<~SH
      #!/bin/sh
      echo 1.2.3
    SH
    chmod 0755, testpath/"bin/session-manager-plugin"
    ENV.prepend_path "PATH", testpath/"bin"

    assert_match "usage", shell_output("#{bin}/ec2-juggle --help")
    assert_match "usage", shell_output("#{bin}/ecs-juggle --help")
  end
end
